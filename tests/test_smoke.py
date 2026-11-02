"""Fast local API smoke tests. Ollama is mocked so tests need no model download."""
import os
import tempfile
import unittest
from unittest.mock import patch

_TEST_ROOT = tempfile.TemporaryDirectory(prefix="careerpilot-tests-")
os.environ["CAREERPILOT_DB_PATH"] = os.path.join(_TEST_ROOT.name, "test.db")
os.environ["CAREERPILOT_KNOWLEDGE_DIR"] = os.path.join(_TEST_ROOT.name, "knowledge")
os.environ["CAREERPILOT_SECRET"] = "test-secret-key-for-local-tests-only"
os.environ["CAREERPILOT_MODEL"] = "test-model"

from app import app  # noqa: E402


class CareerPilotSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        self.client = app.test_client()
        self.username = f"student_{id(self)}"
        response = self.client.post("/api/register", json={"username": self.username, "password": "testpass123"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = self.client.post("/api/profile", json={
            "name": "Test Student",
            "college": "Demo College",
            "target_role": "java full stack developer",
            "skills": "Java, SQL, Git",
            "experience_level": "Beginner",
            "goals": "Get placement in a product company",
            "certifications": "",
            "projects": "Hotel Room API"
        })
        self.assertEqual(response.status_code, 200)

    def test_auth_profile_and_dashboard(self):
        me = self.client.get("/api/me")
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.get_json()["logged_in"])
        self.assertEqual(me.get_json()["profile"]["target_role"], "java full stack developer")
        self.assertEqual(self.client.get("/api/dashboard").status_code, 200)

    def test_chat_is_contextual_and_history_persists(self):
        from services import save_analysis
        from flask import session
        with self.client.session_transaction() as sess:
            user_id = sess["user_id"]
        save_analysis(user_id, {
            "skills": {"coverage": 30, "matched": ["Java", "SQL"], "gaps": ["OOP", "Collections", "Spring Boot"]},
            "learning": {"tasks": [{"day": 1, "skill": "OOP", "task": "Refactor a Java class to use encapsulation.", "priority": "High"}]},
            "resume_agent": {"health": 64, "suggestions": ["Add measurable project outcomes."]}
        })
        with patch("ollama_client.generate", return_value=("", False)):
            response = self.client.post("/api/chat", json={"message": "What should I learn first?"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertIn("OOP", payload["answer"])
        self.assertEqual(payload["mode"], "contextual_fallback")
        history = self.client.get("/api/chat/history").get_json()["messages"]
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[-1]["role"], "assistant")

    def test_chat_fallback_varies_by_question_topic(self):
        from services import save_analysis
        with self.client.session_transaction() as sess:
            user_id = sess["user_id"]
        save_analysis(user_id, {
            "skills": {"coverage": 30, "matched": ["Java", "SQL"], "gaps": ["OOP", "Collections", "Spring Boot"]},
            "learning": {"tasks": [{"day": 1, "skill": "OOP", "task": "Practise encapsulation.", "priority": "High"}]}
        })
        with patch("ollama_client.generate", return_value=("", False)):
            java = self.client.post("/api/chat", json={"message": "How do I improve Java?"}).get_json()["answer"]
            sql = self.client.post("/api/chat", json={"message": "How should I practise SQL?"}).get_json()["answer"]
            project = self.client.post("/api/chat", json={"message": "What project should I build?"}).get_json()["answer"]
        self.assertNotEqual(java, sql)
        self.assertNotEqual(sql, project)
        self.assertIn("Java", java)
        self.assertIn("SELECT", sql)
        self.assertIn("README", project)

    def test_learning_roadmap_status_persists(self):
        generated = self.client.post("/api/learning-tasks/generate", json={})
        self.assertEqual(generated.status_code, 200, generated.get_data(as_text=True))
        tasks = generated.get_json()["tasks"]
        self.assertTrue(tasks)
        task = tasks[0]
        updated = self.client.post(f"/api/learning-tasks/{task['id']}/status", json={"status": "In Progress"})
        self.assertEqual(updated.status_code, 200, updated.get_data(as_text=True))
        reread = self.client.get("/api/learning-tasks").get_json()["tasks"]
        status = next(t["status"] for t in reread if t["id"] == task["id"])
        self.assertEqual(status, "In Progress")

    def test_invalid_chat_and_progress_payloads_are_rejected(self):
        self.assertEqual(self.client.post("/api/chat", json={"message": ""}).status_code, 400)
        self.assertEqual(self.client.post("/api/progress", json={"skill": "Java", "score": "not-a-number"}).status_code, 400)

    def test_resume_upload_and_csv_export(self):
        resume = ("Student Name\nstudent@example.com\nSkills: Java, SQL, Git\nExperience\n" 
                  "Projects\nDeveloped a Java REST API and improved response time by 20%.\nEducation\n" + "Java project practice " * 80)
        response = self.client.post('/api/resume', data={
            'resume': ( __import__('io').BytesIO(resume.encode('utf-8')), 'resume.txt')
        }, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertGreater(response.get_json()['analysis']['score'], 0)
        stored = self.client.get('/api/resume').get_json()['resume']
        self.assertEqual(stored['filename'], 'resume.txt')
        exported = self.client.get('/api/report.csv')
        self.assertEqual(exported.status_code, 200)
        self.assertIn('text/csv', exported.content_type)
        self.assertIn('CareerPilot AI Career Report', exported.get_data(as_text=True))

    def test_project_and_application_crud_is_user_scoped(self):
        created = self.client.post('/api/projects', json={'title':'Demo API','description':'REST project','skills':'Java','status':'Planned'})
        self.assertEqual(created.status_code, 200)
        project = self.client.get('/api/projects').get_json()['projects'][0]
        updated = self.client.put(f"/api/projects/{project['id']}", json={'title':'Updated API','status':'Completed'})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()['project']['title'], 'Updated API')
        self.assertEqual(self.client.delete(f"/api/projects/{project['id']}").status_code, 200)
        self.assertEqual(self.client.delete('/api/applications/999999').status_code, 404)

    def test_interview_returns_answer_level_rubric(self):
        response = self.client.post('/api/interview/submit', json={
            'role':'Java Developer','difficulty':'Beginner',
            'questions':['Explain a project'],
            'answers':['For example, I developed a Java API. Because validation prevented bad input, tests passed and the result improved reliability.']
        })
        self.assertEqual(response.status_code, 200)
        result = response.get_json()['result']
        self.assertIn('rubric', result)
        self.assertEqual(len(result['rubric']), 1)
        self.assertIn('criteria', result['rubric'][0])

    def test_job_match_understands_common_skill_aliases(self):
        from services import job
        from flask import session
        with self.client.session_transaction() as sess:
            user_id = sess['user_id']
        result = job(user_id, 'We need a developer with RESTful APIs, Hibernate, and JavaScript experience.', {
            'skills': 'REST API, JPA, JS'
        })
        self.assertGreaterEqual(result['match'], 66)
        self.assertIn('REST APIs', result['matched'])

    def test_project_update_cannot_cross_user_boundary(self):
        self.client.post('/api/projects', json={'title':'Private project'})
        project = self.client.get('/api/projects').get_json()['projects'][0]
        second = app.test_client()
        self.assertEqual(second.post('/api/register', json={'username':'other_user_unique','password':'testpass123'}).status_code, 200)
        self.assertEqual(second.delete(f"/api/projects/{project['id']}").status_code, 404)

    def test_logout_protects_private_routes(self):
        self.assertEqual(self.client.post("/api/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard").status_code, 401)
        self.assertEqual(self.client.get("/api/chat/history").status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
