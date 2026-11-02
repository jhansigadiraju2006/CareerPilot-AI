from flask import Flask,render_template,request,jsonify,session,Response
import sqlite3
import os
import csv
import io
import re
from werkzeug.utils import secure_filename
from config import SECRET_KEY
from db import get_db
from security import hash_password,verify_password
from services import profile,save_profile,latest,save_analysis,job,chat,chat_history
from orchestrator import Orchestrator
import json
app=Flask(__name__)
app.secret_key=SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=4 * 1024 * 1024)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('CAREERPILOT_COOKIE_SECURE', 'false').lower() == 'true'

def uid(): return session.get('user_id')
def need(): return jsonify(ok=False,error='Please log in first.'),401

def logged(): return bool(uid())

@app.get('/')
def home(): return render_template('index.html')

@app.post('/api/register')
def register():
    d=request.get_json() or {};u=d.get('username','').strip();p=d.get('password','')
    if len(u)<3 or len(p)<4:return jsonify(ok=False,error='Username must be at least 3 characters and password at least 4 characters.'),400
    try:
        with get_db() as c:
            r=c.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',(u,hash_password(p)))
            c.execute('INSERT INTO profiles(user_id) VALUES(?)',(r.lastrowid,));session['user_id']=r.lastrowid;session['username']=u
        return jsonify(ok=True,message='Account created and logged in.')
    except sqlite3.IntegrityError:return jsonify(ok=False,error='Username already exists.'),409
    except Exception:return jsonify(ok=False,error='Account could not be created. Please try again.'),500

@app.post('/api/login')
def login():
    d=request.get_json() or {}
    with get_db() as c:r=c.execute('SELECT * FROM users WHERE username=?',(d.get('username','').strip(),)).fetchone()
    if not r or not verify_password(d.get('password',''),r['password_hash']):return jsonify(ok=False,error='Invalid username or password.'),401
    session.clear()
    session['user_id']=r['id'];session['username']=r['username'];return jsonify(ok=True,message='Logged in.')

@app.post('/api/logout')
def logout(): session.clear();return jsonify(ok=True)

@app.get('/api/me')
def me():
    if not uid():return jsonify(logged_in=False)
    return jsonify(logged_in=True,username=session['username'],profile=profile(uid()),analysis=latest(uid()))

@app.post('/api/profile')
def prof():
    if not uid():return need()
    d=request.get_json() or {};save_profile(uid(),d);return jsonify(ok=True,profile=profile(uid()))

@app.post('/api/analyze')
def analyze():
    if not uid():return need()
    p=profile(uid())
    if not p.get('name') or not p.get('target_role'):return jsonify(ok=False,error='Please enter Name and Target Role in Student Profile.'),400
    try:
        a=Orchestrator(uid()).analyze(p);save_analysis(uid(),a);return jsonify(ok=True,analysis=a)
    except Exception as e:return jsonify(ok=False,error=f'Career Intelligence failed: {type(e).__name__}: {e}'),500

@app.get('/api/dashboard')
def dashboard():
    if not uid():return need()
    with get_db() as c:
        acts=[dict(x) for x in c.execute('SELECT agent,action,status,details,created_at FROM activities WHERE user_id=? ORDER BY id DESC LIMIT 30',(uid(),)).fetchall()]
        apps=[dict(x) for x in c.execute('SELECT company,role,status,match_score,notes,created_at FROM applications WHERE user_id=? ORDER BY id DESC LIMIT 20',(uid(),)).fetchall()]
        interviews=[dict(x) for x in c.execute('SELECT role,difficulty,score,feedback,created_at FROM interviews WHERE user_id=? ORDER BY id DESC LIMIT 10',(uid(),)).fetchall()]
        progress=[dict(x) for x in c.execute('SELECT skill,score,source,created_at FROM progress WHERE user_id=? ORDER BY id DESC LIMIT 30',(uid(),)).fetchall()]
    return jsonify(ok=True,profile=profile(uid()),analysis=latest(uid()),activity=acts,applications=apps,interviews=interviews,progress=progress)

@app.post('/api/job')
def job_api():
    if not uid():return need()
    d=request.get_json() or {};t=d.get('job_text','').strip()
    if not t:return jsonify(ok=False,error='Paste a job description first.'),400
    return jsonify(ok=True,result=job(uid(),t,profile(uid())))

@app.post('/api/chat')
def chat_api():
    if not uid():return need()
    m=str((request.get_json() or {}).get('message','')).strip()
    if not m:return jsonify(ok=False,error='Enter a question.'),400
    if len(m)>4000:return jsonify(ok=False,error='Please keep the question under 4,000 characters.'),400
    return jsonify(ok=True,**chat(uid(),m))

@app.get('/api/chat/history')
def chat_history_api():
    if not uid():return need()
    return jsonify(ok=True,messages=chat_history(uid()))

@app.post('/api/simulate')
def simulate():
    if not uid():return need()
    d=request.get_json() or {};target=str(d.get('target_role') or profile(uid()).get('target_role') or 'Software Developer').strip();added=[x.strip() for x in str(d.get('added_skills') or '').split(',') if x.strip()]
    from agents.agents import SkillAgent
    req=SkillAgent.roles.get(target.lower(),SkillAgent.roles['software developer']);p=profile(uid());have={x.strip().lower() for x in p.get('skills','').split(',') if x.strip()};before=round(len([s for s in req if s.lower() in have])*100/len(req));new=have|{x.lower() for x in added};g=[s for s in req if s.lower() not in new];after=round((len(req)-len(g))*100/len(req))
    with get_db() as c:c.execute('INSERT INTO simulations(user_id,target_role,added_skills,coverage_before,coverage_after,gaps_json) VALUES(?,?,?,?,?,?)',(uid(),target,', '.join(added),before,after,json.dumps(g)))
    return jsonify(ok=True,scenario={'target':target,'required':req,'added':added,'coverage_before':before,'coverage_after':after,'gaps':g})

@app.post('/api/interview/start')
def interview_start():
    if not uid():return need()
    d=request.get_json() or {};role=d.get('role') or profile(uid()).get('target_role') or 'Software Developer';difficulty=d.get('difficulty','Intermediate')
    questions=[f'Why are you interested in {role}?','Explain a project where you solved a difficult technical problem.','How would you test and debug a feature in production?','What is one trade-off you made in a project and why?',f'Which {role} skill are you improving right now?']
    return jsonify(ok=True,role=role,difficulty=difficulty,questions=questions)

@app.post('/api/interview/submit')
def interview_submit():
    if not uid():return need()
    d=request.get_json() or {};answers=d.get('answers',[]);questions=d.get('questions',[]);role=str(d.get('role') or profile(uid()).get('target_role') or 'Software Developer')[:160];difficulty=str(d.get('difficulty') or 'Intermediate')[:40]
    if not isinstance(answers,list) or not isinstance(questions,list):return jsonify(ok=False,error='Answers and questions must be lists.'),400
    answers=[str(x)[:5000] for x in answers[:20]];questions=[str(x)[:1000] for x in questions[:20]]
    rubric=[]
    for idx, answer in enumerate(answers):
        text = str(answer).strip(); low = text.casefold(); words = re.findall(r'\b[\w+#.-]+\b', text)
        criteria = {
            'answer_detail': min(25, round(len(words) / 4)),
            'specific_example': 25 if any(term in low for term in ('for example', 'for instance', 'project', 'implemented', 'built', 'developed')) else 8 if len(words) >= 20 else 0,
            'technical_reasoning': 25 if any(term in low for term in ('because', 'trade-off', 'tradeoff', 'debug', 'test', 'design', 'database', 'api', 'algorithm', 'performance')) else 8 if len(words) >= 25 else 0,
            'outcome_or_learning': 25 if any(term in low for term in ('result', 'improved', 'reduced', 'increased', 'learned', 'outcome', '%')) else 8 if len(words) >= 30 else 0,
        }
        q = questions[idx] if idx < len(questions) else f'Answer {idx+1}'
        rubric.append({'question': q, 'score': min(100, sum(criteria.values())), 'criteria': criteria,
                       'feedback': 'Add a concrete example, explain why you chose your approach, and finish with a result or lesson.' if sum(criteria.values()) < 70 else 'Good detail. Make the outcome and your personal contribution explicit.'})
    score = round(sum(x['score'] for x in rubric) / len(rubric)) if rubric else 0
    fb = ('Strong structured practice answers. Keep the examples concise and measurable.' if score >= 70 else 'Practice using a situation, action, technical reasoning, and result structure. This score is a practice aid, not a hiring prediction.')
    with get_db() as c:c.execute('INSERT INTO interviews(user_id,role,difficulty,score,feedback,questions_json) VALUES(?,?,?,?,?,?)',(uid(),role,difficulty,score,fb,json.dumps(questions)))
    return jsonify(ok=True,result={'score':score,'feedback':fb,'rubric':rubric,
        'strengths':['Detailed answers' if score>=70 else 'You completed the practice round'],
        'improvements':['Use a concrete project example','Explain technical trade-offs','State measurable outcomes or lessons','Use a clear situation-action-result structure'],
        'disclaimer':'Practice-only rubric; not a validated hiring or employability prediction.'})

@app.post('/api/projects')
def projects():
    if not uid():return need()
    d=request.get_json() or {};title=d.get('title','').strip();desc=d.get('description','').strip();skills=d.get('skills','').strip()
    if not title:return jsonify(ok=False,error='Project title is required.'),400
    with get_db() as c:c.execute('INSERT INTO projects(user_id,title,description,skills,status) VALUES(?,?,?,?,?)',(uid(),title,desc,skills,d.get('status','Planned')))
    return jsonify(ok=True)

@app.get('/api/projects')
def get_projects():
    if not uid():return need()
    with get_db() as c:r=[dict(x) for x in c.execute('SELECT * FROM projects WHERE user_id=? ORDER BY id DESC',(uid(),)).fetchall()]
    return jsonify(ok=True,projects=r)

@app.post('/api/applications')
def applications():
    if not uid():return need()
    d=request.get_json() or {}
    company=str(d.get('company') or '').strip(); role=str(d.get('role') or '').strip(); status=str(d.get('status') or 'Applied').strip()
    if not company or not role:return jsonify(ok=False,error='Company and role are required.'),400
    try: score=max(0,min(100,int(d.get('match_score',0) or 0)))
    except (TypeError,ValueError):return jsonify(ok=False,error='Match score must be a number from 0 to 100.'),400
    if status not in ('Interested','Applied','Screening','Assessment','Interview','Offer','Rejected','Withdrawn'):status='Applied'
    with get_db() as c:c.execute('INSERT INTO applications(user_id,company,role,status,match_score,notes) VALUES(?,?,?,?,?,?)',(uid(),company[:160],role[:160],status,score,str(d.get('notes') or '')[:2000]))
    return jsonify(ok=True)

@app.get('/api/applications')
def get_applications():
    if not uid():return need()
    with get_db() as c:r=[dict(x) for x in c.execute('SELECT * FROM applications WHERE user_id=? ORDER BY id DESC',(uid(),)).fetchall()]
    return jsonify(ok=True,applications=r)

@app.route('/api/projects/<int:project_id>', methods=['PUT', 'PATCH', 'DELETE'])
def project_detail(project_id):
    if not uid(): return need()
    with get_db() as c:
        row = c.execute('SELECT * FROM projects WHERE id=? AND user_id=?', (project_id, uid())).fetchone()
        if not row: return jsonify(ok=False, error='Project not found.'), 404
        if request.method == 'DELETE':
            c.execute('DELETE FROM projects WHERE id=? AND user_id=?', (project_id, uid()))
            return jsonify(ok=True, message='Project deleted.')
        d = request.get_json() or {}
        title = str(d.get('title', row['title']) or '').strip()
        if not title: return jsonify(ok=False, error='Project title is required.'), 400
        status = str(d.get('status', row['status']) or 'Planned')
        if status not in ('Planned', 'In Progress', 'Completed', 'Deployed'): status = 'Planned'
        c.execute('UPDATE projects SET title=?, description=?, skills=?, status=? WHERE id=? AND user_id=?',
                  (title[:180], str(d.get('description', row['description']) or '')[:4000],
                   str(d.get('skills', row['skills']) or '')[:1000], status, project_id, uid()))
        updated = c.execute('SELECT * FROM projects WHERE id=? AND user_id=?', (project_id, uid())).fetchone()
    return jsonify(ok=True, project=dict(updated))


@app.route('/api/applications/<int:application_id>', methods=['PUT', 'PATCH', 'DELETE'])
def application_detail(application_id):
    if not uid(): return need()
    with get_db() as c:
        row = c.execute('SELECT * FROM applications WHERE id=? AND user_id=?', (application_id, uid())).fetchone()
        if not row: return jsonify(ok=False, error='Application not found.'), 404
        if request.method == 'DELETE':
            c.execute('DELETE FROM applications WHERE id=? AND user_id=?', (application_id, uid()))
            return jsonify(ok=True, message='Application deleted.')
        d = request.get_json() or {}
        company = str(d.get('company', row['company']) or '').strip()
        role = str(d.get('role', row['role']) or '').strip()
        status = str(d.get('status', row['status']) or 'Applied').strip()
        if not company or not role: return jsonify(ok=False, error='Company and role are required.'), 400
        allowed = ('Interested', 'Applied', 'Screening', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
        if status not in allowed: return jsonify(ok=False, error='Invalid application status.'), 400
        try: score = max(0, min(100, int(d.get('match_score', row['match_score']) or 0)))
        except (TypeError, ValueError): return jsonify(ok=False, error='Match score must be 0–100.'), 400
        notes = str(d.get('notes', row['notes']) or '')[:2000]
        c.execute('UPDATE applications SET company=?, role=?, status=?, match_score=?, notes=? WHERE id=? AND user_id=?',
                  (company[:160], role[:160], status, score, notes, application_id, uid()))
        updated = c.execute('SELECT * FROM applications WHERE id=? AND user_id=?', (application_id, uid())).fetchone()
    return jsonify(ok=True, application=dict(updated))


def _extract_resume_text(filename, raw):
    # Extraction is local; resume contents are not sent to a third party.
    suffix = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if suffix == 'txt':
        return raw.decode('utf-8-sig', errors='replace')
    if suffix == 'pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        except ImportError:
            raise ValueError('PDF parsing dependency is missing. Run SETUP_AND_RUN.bat to install requirements.')
        except Exception:
            raise ValueError('Could not read this PDF. Try a text-based PDF or upload a .txt file.')
    if suffix == 'docx':
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw))
            return '\n'.join(par.text for par in doc.paragraphs)
        except ImportError:
            raise ValueError('DOCX parsing dependency is missing. Run SETUP_AND_RUN.bat to install requirements.')
        except Exception:
            raise ValueError('Could not read this DOCX file. Please check that it is a valid Word document.')
    raise ValueError('Supported resume formats are .txt, .pdf, and .docx.')


def _resume_score(text):
    low = text.casefold()
    sections = {
        'contact information': bool(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', text)),
        'skills section': bool(re.search(r'\b(skills|technical skills|technologies)\b', low)),
        'experience or internship': bool(re.search(r'\b(experience|internship|employment)\b', low)),
        'projects section': bool(re.search(r'\b(projects|academic projects)\b', low)),
        'education section': bool(re.search(r'\b(education|degree|university|college)\b', low)),
        'achievement evidence': bool(re.search(r'\b(achieved|improved|reduced|increased|built|developed|deployed|%|users)\b', low)),
    }
    words = re.findall(r"[A-Za-z][A-Za-z+#.\-/]*", text)
    suggestions = [f'Add a clear {name} section.' for name, found in sections.items() if not found]
    if len(words) < 120: suggestions.append('Add more detail about projects, technical decisions, and outcomes; the extracted resume is quite short.')
    if len(words) > 1000: suggestions.append('Consider shortening the resume and prioritizing role-relevant evidence.')
    score = round(sum(sections.values()) * 100 / len(sections))
    return {'score': score, 'word_count': len(words), 'sections': sections,
            'suggestions': suggestions or ['The basic structure looks complete. Tailor skills and measurable outcomes to each job description.'],
            'disclaimer': 'This is a local structure check, not an official ATS score or a guarantee of interview selection.'}


@app.post('/api/resume')
def upload_resume():
    if not uid(): return need()
    upload = request.files.get('resume')
    if not upload or not upload.filename: return jsonify(ok=False, error='Choose a resume file first.'), 400
    filename = secure_filename(upload.filename) or 'resume'
    raw = upload.read(3 * 1024 * 1024 + 1)
    if not raw: return jsonify(ok=False, error='The uploaded file is empty.'), 400
    if len(raw) > 3 * 1024 * 1024: return jsonify(ok=False, error='Resume files must be 3 MB or smaller.'), 413
    try: extracted = _extract_resume_text(filename, raw).strip()
    except ValueError as exc: return jsonify(ok=False, error=str(exc)), 400
    if not extracted: return jsonify(ok=False, error='No selectable text was found. Scanned image PDFs are not supported yet; try a text-based PDF or .txt file.'), 400
    if len(extracted) > 100000: extracted = extracted[:100000]
    analysis = _resume_score(extracted)
    with get_db() as c:
        c.execute("INSERT INTO resume_documents(user_id, filename, extracted_text, analysis_json, updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET filename=excluded.filename, extracted_text=excluded.extracted_text, analysis_json=excluded.analysis_json, updated_at=CURRENT_TIMESTAMP", (uid(), filename, extracted, json.dumps(analysis)))
    return jsonify(ok=True, filename=filename, analysis=analysis)


@app.get('/api/resume')
def get_resume():
    if not uid(): return need()
    with get_db() as c:
        row = c.execute('SELECT filename, analysis_json, updated_at FROM resume_documents WHERE user_id=?', (uid(),)).fetchone()
    if not row: return jsonify(ok=True, resume=None)
    return jsonify(ok=True, resume={'filename': row['filename'], 'analysis': json.loads(row['analysis_json']), 'updated_at': row['updated_at']})


@app.get('/api/report.csv')
def export_report_csv():
    if not uid(): return need()
    user_profile = profile(uid()); analysis = latest(uid()) or {}
    output = io.StringIO(newline=''); writer = csv.writer(output)
    writer.writerow(['CareerPilot AI Career Report'])
    writer.writerow(['Generated at', __import__('datetime').datetime.now().isoformat(timespec='seconds')])
    writer.writerow(['Name', user_profile.get('name', '')]); writer.writerow(['College', user_profile.get('college', '')])
    writer.writerow(['Target role', user_profile.get('target_role', '')]); writer.writerow(['Current skills', user_profile.get('skills', '')])
    writer.writerow(['Experience level', user_profile.get('experience_level', '')])
    writer.writerow(['Summary', analysis.get('summary', 'Run Career Intelligence first.')])
    skills = analysis.get('skills') or {}
    writer.writerow([]); writer.writerow(['Skill coverage (%)', skills.get('coverage', '')])
    writer.writerow(['Matched skills']); [writer.writerow([x]) for x in (skills.get('matched') or [])]
    writer.writerow(['Skill gaps']); [writer.writerow([x]) for x in (skills.get('gaps') or [])]
    with get_db() as c:
        writer.writerow([]); writer.writerow(['Learning roadmap']); writer.writerow(['Week', 'Skill', 'Task', 'Priority', 'Status'])
        for r in c.execute('SELECT week_number, skill, task, priority, status FROM learning_tasks WHERE user_id=? ORDER BY week_number,id', (uid(),)): writer.writerow(list(r))
        writer.writerow([]); writer.writerow(['Applications']); writer.writerow(['Company', 'Role', 'Status', 'Match score', 'Notes', 'Created'])
        for r in c.execute('SELECT company,role,status,match_score,notes,created_at FROM applications WHERE user_id=? ORDER BY id DESC', (uid(),)): writer.writerow(list(r))
        writer.writerow([]); writer.writerow(['Portfolio projects']); writer.writerow(['Title', 'Description', 'Skills', 'Status', 'Created'])
        for r in c.execute('SELECT title,description,skills,status,created_at FROM projects WHERE user_id=? ORDER BY id DESC', (uid(),)): writer.writerow(list(r))
        writer.writerow([]); writer.writerow(['Mock interviews']); writer.writerow(['Role', 'Difficulty', 'Score', 'Feedback', 'Created'])
        for r in c.execute('SELECT role,difficulty,score,feedback,created_at FROM interviews WHERE user_id=? ORDER BY id DESC', (uid(),)): writer.writerow(list(r))
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=careerpilot-career-report.csv'})



@app.post('/api/progress')
def add_progress():
    if not uid():return need()
    d=request.get_json() or {};skill=str(d.get('skill') or '').strip()
    try:score=max(0,min(100,int(d.get('score',0))))
    except (TypeError,ValueError):return jsonify(ok=False,error='Score must be a number from 0 to 100.'),400
    if not skill:return jsonify(ok=False,error='Skill is required.'),400
    with get_db() as c:c.execute('INSERT INTO progress(user_id,skill,score,source) VALUES(?,?,?,?)',(uid(),skill,score,d.get('source','manual')))
    return jsonify(ok=True)


@app.get('/api/learning-tasks')
def get_learning_tasks():
    if not uid():
        return need()

    with get_db() as c:
        tasks = [
            dict(row) for row in c.execute(
                '''SELECT id, target_role, week_number, skill, task,
                          priority, status, created_at, updated_at
                   FROM learning_tasks
                   WHERE user_id = ?
                   ORDER BY week_number, id''',
                (uid(),)
            ).fetchall()
        ]

    return jsonify(ok=True, tasks=tasks)


@app.post('/api/learning-tasks/generate')
def generate_learning_tasks():
    if not uid():
        return need()

    p = profile(uid())
    role = p.get('target_role') or 'Software Developer'

    # Preserve existing tasks and completed progress.
    with get_db() as c:
        existing = c.execute(
            'SELECT COUNT(*) AS total FROM learning_tasks WHERE user_id = ?',
            (uid(),)
        ).fetchone()['total']

    if existing:
        return get_learning_tasks()

    # Reuse career analysis tasks when available.
    analysis = latest(uid()) or {}
    learning = analysis.get('learning') or {}
    planned_tasks = learning.get('tasks') or []

    # Generate tasks if no analysis tasks exist.
    if not planned_tasks:
        from agents.agents import SkillAgent, LearningAgent

        skills = SkillAgent().run({'profile': p})
        learning = LearningAgent().run({
            'profile': p,
            'skills': skills
        })
        planned_tasks = learning.get('tasks', [])

    if not planned_tasks:
        return jsonify(
            ok=False,
            error='No learning tasks could be generated. Please check your profile.'
        ), 400

    with get_db() as c:
        elapsed_days = 0

        for item in planned_tasks:
            try:
                estimated_days = max(
                    1, int(item.get('estimated_days', 1))
                )
            except (TypeError, ValueError):
                estimated_days = 1

            
            week = (elapsed_days // 5) + 1
            elapsed_days += estimated_days


            skill = str(item.get('skill') or 'Core Skills').strip()
            task = str(item.get('task') or f'Practice {skill}').strip()
            priority = str(item.get('priority') or 'Medium').strip()
            evidence = str(item.get('evidence') or '').strip()

            if evidence:
                task = f'{task} Expected evidence: {evidence}'

            c.execute(
                '''INSERT INTO learning_tasks
                   (user_id, target_role, week_number, skill, task, priority)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (uid(), role, week, skill, task, priority)
            )

    return get_learning_tasks()

@app.post('/api/learning-tasks/<int:task_id>/status')
def update_learning_task_status(task_id):
    if not uid():
        return need()

    data = request.get_json() or {}
    status = data.get('status', '')

    allowed_statuses = ('Not Started', 'In Progress', 'Completed')
    if status not in allowed_statuses:
        return jsonify(
            ok=False,
            error='Status must be Not Started, In Progress, or Completed.'
        ), 400

    with get_db() as c:
        result = c.execute(
            '''UPDATE learning_tasks
               SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?''',
            (status, task_id, uid())
        )

        if result.rowcount == 0:
            return jsonify(
                ok=False,
                error='Task not found in your account.'
            ), 404

        row = c.execute(
            '''SELECT id, target_role, week_number, skill, task,
                      priority, status, created_at, updated_at
               FROM learning_tasks
               WHERE id = ? AND user_id = ?''',
            (task_id, uid())
        ).fetchone()

    return jsonify(ok=True, task=dict(row))

@app.post('/api/feedback')
def save_feedback():
    if not uid():
        return need()

    data = request.get_json() or {}
    rating = str(data.get('rating', '')).strip()
    context = str(data.get('context', 'CareerPilot')).strip()

    if rating not in ('useful', 'needs-work'):
        return jsonify(
            ok=False,
            error='Rating must be useful or needs-work.'
        ), 400

    with get_db() as c:
        c.execute(
            'INSERT INTO feedback (user_id, rating, context) VALUES (?, ?, ?)',
            (uid(), rating, context)
        )

    return jsonify(ok=True, message='Feedback saved.')


@app.get('/api/evaluation')
def evaluation():
    if not uid():
        return need()

    user_id = uid()

    with get_db() as c:
        total = c.execute(
            'SELECT COUNT(*) FROM activities WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]

        failures = c.execute(
            """SELECT COUNT(*) FROM activities
               WHERE user_id = ? AND LOWER(status) = 'error'""",
            (user_id,)
        ).fetchone()[0]

        conversations = c.execute(
            'SELECT COUNT(*) FROM conversations WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]

        feedback_count = c.execute(
            'SELECT COUNT(*) FROM feedback WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]

        interviews = c.execute(
            'SELECT COUNT(*) FROM interviews WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]

        applications = c.execute(
            'SELECT COUNT(*) FROM applications WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]

    success_rate = round((total - failures) * 100 / total) if total else 100

    return jsonify(
        ok=True,
        metrics={
            'agent_runs': total,
            'agent_failures': failures,
            'agent_success_rate': success_rate,
            'conversation_messages': conversations,
            'feedback_items': feedback_count,
            'mock_interviews': interviews,
            'tracked_applications': applications
        }
    )


@app.get('/api/report')
def career_report():
    if not uid():
        return need()

    user_id = uid()
    user_profile = profile(user_id)
    analysis = latest(user_id) or {}

    with get_db() as c:
        interviews = [
            dict(row) for row in c.execute(
                """SELECT role, difficulty, score, feedback, created_at
                   FROM interviews
                   WHERE user_id = ?
                   ORDER BY id DESC LIMIT 5""",
                (user_id,)
            ).fetchall()
        ]

        applications = [
            dict(row) for row in c.execute(
                """SELECT company, role, status, match_score, notes, created_at
                   FROM applications
                   WHERE user_id = ?
                   ORDER BY id DESC LIMIT 10""",
                (user_id,)
            ).fetchall()
        ]

        projects = [
            dict(row) for row in c.execute(
                """SELECT title, description, skills, status, created_at
                   FROM projects
                   WHERE user_id = ?
                   ORDER BY id DESC LIMIT 10""",
                (user_id,)
            ).fetchall()
        ]

    with get_db() as c:
        resume_row = c.execute('SELECT filename, analysis_json, updated_at FROM resume_documents WHERE user_id=?', (user_id,)).fetchone()
    resume_data = None
    if resume_row:
        try: resume_data = {'filename': resume_row['filename'], 'analysis': json.loads(resume_row['analysis_json']), 'updated_at': resume_row['updated_at']}
        except (TypeError, ValueError): resume_data = {'filename': resume_row['filename'], 'analysis': {}, 'updated_at': resume_row['updated_at']}

    report_data = {
        'title': 'CareerPilot AI - Career Intelligence Report',
        'uploaded_resume': resume_data,
        'generated_for': user_profile,
        'executive_summary': analysis.get(
            'summary', 'Run Career Intelligence to generate your analysis.'
        ),
        'skill_analysis': analysis.get('skills', {}),
        'learning_plan': analysis.get('learning', {}),
        'resume_analysis': analysis.get('resume_agent', {}),
        'placement_readiness': analysis.get('placement_agent', {}),
        'digital_twin': analysis.get('digital_twin', {}),
        'explainability': analysis.get('explainability', []),
        'interviews': interviews,
        'applications': applications,
        'projects': projects
    }

    return jsonify(ok=True, report=report_data)



if __name__ == '__main__':
    app.run(debug=os.getenv('CAREERPILOT_DEBUG', 'false').lower() == 'true', host='127.0.0.1', port=5000)

