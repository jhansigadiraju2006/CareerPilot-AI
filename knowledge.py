from pathlib import Path
import re
from config import KNOWLEDGE_DIR
DEFAULT={
'java_backend.txt':'''Java backend roadmap: Core Java, OOP, collections, exceptions, streams and concurrency should lead into SQL, REST APIs, Spring Boot, JPA/Hibernate, testing, Git and Docker.''',
'devops.txt':'''DevOps roadmap: Linux/Unix, shell commands, networking, Git, Docker, CI/CD, cloud fundamentals and Kubernetes. Learn Linux permissions, processes and networking before advanced automation.''',
'interview.txt':'''Interview preparation should combine coding, core CS, project explanation and timed mock interviews. Java interviews commonly cover OOP, collections, exceptions, JVM basics, SQL, REST and Spring.''',
'resume.txt':'''A technical resume should emphasize relevant skills, measurable project outcomes, certifications and links. Align evidence with the target role.'''}
def ensure():
    KNOWLEDGE_DIR.mkdir(parents=True,exist_ok=True)
    for n,t in DEFAULT.items():
        p=KNOWLEDGE_DIR/n
        if not p.exists():p.write_text(t,encoding='utf-8')
def toks(x):return set(re.findall(r'[a-zA-Z0-9+#.]+',x.lower()))
def retrieve(q,k=3):
    ensure(); qt=toks(q); out=[]
    for p in KNOWLEDGE_DIR.glob('*.txt'):
        t=p.read_text(encoding='utf-8',errors='ignore'); s=len(qt&toks(t))
        if s:out.append((s,p.name,t))
    out.sort(reverse=True); return [{'source':n,'score':s,'text':t} for s,n,t in out[:k]]
