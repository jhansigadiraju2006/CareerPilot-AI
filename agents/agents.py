from collections import Counter

class CareerAgent:
    name='Career Agent'
    def run(self,c):
        p=c['profile']; role=p.get('target_role') or 'Software Developer'
        level=p.get('experience_level','Beginner')
        directions={'Beginner':'Build fundamentals, one strong project and interview basics.','Intermediate':'Deepen system design, production practices and role-specific projects.','Advanced':'Demonstrate architecture, leadership, optimization and measurable impact.'}
        return {'target':role,'level':level,'direction':directions.get(level,directions['Beginner']),'milestones':['Core skills','Portfolio evidence','Interview readiness','Job applications']}

class SkillAgent:
    name='Skill Agent'
    roles={
      'java full stack developer':['Java','OOP','Collections','SQL','Spring Boot','REST APIs','JPA/Hibernate','Git','Docker','Angular'],
      'java backend developer':['Java','OOP','Collections','SQL','Spring Boot','REST APIs','JPA/Hibernate','Git','Docker'],
      'devops engineer':['Linux','Git','Networking','Docker','CI/CD','Cloud','Kubernetes','Monitoring','Terraform'],
      'data scientist':['Python','SQL','Statistics','Pandas','NumPy','Machine Learning','Visualization','Git','Model Evaluation'],
      'machine learning engineer':['Python','SQL','Statistics','Machine Learning','Deep Learning','APIs','Docker','Git','Model Deployment'],
      'software developer':['Programming','DSA','Git','SQL','Testing','REST APIs','Debugging','OOP','Databases'],
      'frontend developer':['HTML','CSS','JavaScript','React','Git','REST APIs','Testing','Accessibility'],
      'cloud engineer':['Linux','Networking','Cloud','Docker','Kubernetes','Terraform','CI/CD','Security','Monitoring']}
    def run(self,c):
        p=c['profile']; req=self.roles.get(p.get('target_role','').lower(),self.roles['software developer'])
        have={x.strip().lower() for x in p.get('skills','').split(',') if x.strip()}
        gaps=[x for x in req if x.lower() not in have]
        matched=[x for x in req if x.lower() in have]
        cov=round(len(matched)*100/len(req))
        graph=[{'skill':s,'depends_on':req[i-1] if i else None,'status':'matched' if s in matched else 'gap'} for i,s in enumerate(req)]
        return {'required':req,'matched':matched,'gaps':gaps,'coverage':cov,'graph':graph}

class LearningAgent:
    name = 'Learning Agent'
    
    LEARNING_ORDER = [
        'java',
        'oop',
        'collections',
        'dsa',
        'sql',
        'git',
        'spring boot',
        'rest apis',
        'jpa/hibernate',
        'testing',
        'angular',
        'docker',
    ]


    TASK_GUIDES = {
        'java': (
            'Review classes, objects, constructors, encapsulation, inheritance, '
            'polymorphism and abstraction. Implement a small Java example.',
            'A runnable Java example demonstrating at least four OOP concepts.'
        ),
        'oop': (
            'Practice encapsulation, inheritance, polymorphism and abstraction. '
            'Refactor a small program using these concepts.',
            'Source code with comments explaining the OOP concepts used.'
        ),
        'collections': (
            'Practice List, Set, Map and Queue. Solve exercises involving '
            'duplicates, lookup and ordering.',
            'A runnable Java program with tests for List, Set and Map operations.'
        ),
        'sql': (
            'Practice SELECT, JOIN, GROUP BY, subqueries and database constraints '
            'using a small relational schema.',
            'SQL file containing sample tables, data and tested queries.'
        ),
        'spring boot': (
            'Build a small Spring Boot application with a controller, service '
            'and repository layer.',
            'Runnable application with documented endpoints and a successful test.'
        ),
        'rest apis': (
            'Create REST endpoints using appropriate HTTP methods and status codes. '
            'Validate input and handle errors.',
            'Endpoint documentation and request/response tests.'
        ),
        'jpa/hibernate': (
            'Map Java entities to database tables and practice repository queries '
            'and relationships.',
            'Working persistence example with entity and repository tests.'
        ),
        'git': (
            'Practice branches, commits, merge and resolving a simple conflict.',
            'Repository with meaningful commits and a documented workflow.'
        ),
        'docker': (
            'Containerize a small application and configure its runtime settings.',
            'Dockerfile and evidence that the container runs successfully.'
        ),
        'angular': (
            'Build a component-based interface with a form and connect it to an API.',
            'Working UI with a form and a successful API integration.'
        ),
        'dsa': (
            'Solve problems involving arrays, strings, searching and sorting; '
            'explain time and space complexity.',
            'Three tested solutions with complexity notes.'
        ),
        'testing': (
            'Write unit tests for core logic and test expected and invalid inputs.',
            'Automated tests with recorded pass/fail results.'
        )
    }

    def run(self, c):
        raw_gaps = c.get('skills', {}).get('gaps', [])
        gaps = []
        seen = set()

        for skill in raw_gaps:
            label = str(skill).strip()
            key = label.casefold()
            if label and key not in seen:
                gaps.append(label)
                seen.add(key)

        if not gaps:
            gaps = ['Testing', 'Project polishing']
            
        order = {
            skill: index
            for index, skill in enumerate(self.LEARNING_ORDER)
        }

        gaps.sort(
            key=lambda skill: order.get(skill.casefold(), len(order))
        )


        level = str(
            c.get('profile', {}).get('experience_level', 'Beginner')
        ).strip().casefold()

        tasks = []
        for i, skill in enumerate(gaps[:8]):
            key = skill.casefold()
            guide = self.TASK_GUIDES.get(key)

            if guide is None:
                for topic, details in self.TASK_GUIDES.items():
                    if topic in key or key in topic:
                        guide = details
                        break

            if guide is None:
                guide = (
                    f'Learn the core concepts of {skill}, then apply them '
                    'in a small role-relevant exercise.',
                    f'A working example demonstrating {skill}, with a short '
                    'README explaining what you built and tested.'
                )

            study_task, evidence = guide
            days = 2 if level == 'beginner' else 3
            if key in ('spring boot', 'jpa/hibernate', 'docker', 'angular'):
                days += 2
            elif key in ('oop', 'collections', 'dsa', 'sql'):
                days += 1

            tasks.append({
                'day': i + 1,
                'skill': skill,
                'task': study_task,
                'priority': 'High' if i < 2 else ('Medium' if i < 5 else 'Low'),
                'estimated_days': days,
                'evidence': evidence
            })

        return {
            'tasks': tasks,
            'count': len(tasks),
            'weekly_focus': [task['skill'] for task in tasks[:3]]
        }

class ResumeAgent:
    name='Resume Agent'
    def run(self,c):
        p=c['profile']; tips=[]
        if not p.get('projects'): tips.append('Add a role-aligned project with measurable outcomes.')
        if not p.get('certifications'): tips.append('Add relevant certifications, courses or verified training.')
        if len(p.get('skills','').split(','))<4: tips.append('Surface more concrete technical skills relevant to the target role.')
        tips.append('Use action verbs, evidence and measurable results for important claims.')
        health=max(35,100-len(tips)*12)
        return {'health':health,'suggestions':tips,'ats_keywords':c['skills']['required'][:8]}

class PlacementAgent:
    name='Placement Agent'
    def run(self,c):
        skill=c['skills']['coverage']; resume=c['resume_agent']['health']; level=c['profile'].get('experience_level','Beginner')
        bonus={'Beginner':0,'Intermediate':5,'Advanced':8}.get(level,0)
        readiness=min(100,round(skill*.55+resume*.25+20+bonus))
        return {'readiness':readiness,'focus':['Coding practice','Core CS revision','Project explanation','Mock interviews','Targeted applications']}

class InterviewAgent:
    name='Interview Agent'
    def run(self,c):
        role=c['profile'].get('target_role','Software Developer')
        return {'questions':[f'Explain a difficult problem you solved as a {role}.','Describe your project architecture and trade-offs.','How would you debug a production issue?','Which skill in the target role is currently your weakest and how are you improving it?','Describe a time you optimized or improved a system.']}

class ProjectAgent:
    name='Project Agent'
    def run(self,c):
        gaps=c['skills']['gaps'][:3]
        return {'projects':[{'title':f'{c["profile"].get("target_role","Career")} Portfolio Accelerator','skills':gaps or ['Testing','System Design'],'deliverable':'Build, document, test and deploy a small role-aligned application.'}]}

