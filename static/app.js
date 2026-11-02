const $=id=>document.getElementById(id);let A={};
async function api(u,o={}){const isForm=typeof FormData!=='undefined'&&o.body instanceof FormData;const headers={...(isForm?{}:{'Content-Type':'application/json'}),...(o.headers||{})};const r=await fetch(u,{...o,headers});let d={};try{d=await r.json()}catch{}if(!r.ok)throw Error(d.error||'Request failed');return d}
function p(){return{name:$('name').value,college:$('college').value,target_role:$('role').value,skills:$('skills').value,experience_level:$('level').value,goals:$('goals').value,certifications:$('certs').value,projects:$('projects').value}}
async function register(){try{let d=await api('/api/register',{method:'POST',body:JSON.stringify({username:$('user').value,password:$('pass').value})});$('authmsg').textContent=d.message;load()}catch(e){$('authmsg').textContent=e.message}}
async function login(){try{let d=await api('/api/login',{method:'POST',body:JSON.stringify({username:$('user').value,password:$('pass').value})});$('authmsg').textContent=d.message;load()}catch(e){$('authmsg').textContent=e.message}}
async function logout(){await api('/api/logout',{method:'POST'});location.reload()}
async function load(){let d=await api('/api/me');if(!d.logged_in)return;$('status').textContent='Logged in as '+d.username;let p=d.profile||{};[['name','name'],['college','college'],['role','target_role'],['skills','skills'],['goals','goals'],['certs','certifications'],['projects','projects']].forEach(x=>$(x[0]).value=p[x[1]]||'');if(p.experience_level)$('level').value=p.experience_level;if(d.analysis){A=d.analysis;render(A)}await loadDashboard();await loadApplications();await loadInterviews();await loadLearningTasks();await loadChatHistory();await loadResume()}
async function save(){try{await api('/api/profile',{method:'POST',body:JSON.stringify(p())});$('msg').textContent='Profile saved.';return true}catch(e){$('msg').textContent=e.message;return false}}
async function analyze(){try{if(!await save())return;$('msg').textContent='Running 7-agent intelligence pipeline...';let d=await api('/api/analyze',{method:'POST',body:'{}'});A=d.analysis;render(A);$('msg').textContent='Career Intelligence completed.';await loadDashboard();await loadLearningTasks()}catch(e){$('msg').textContent=e.message}}
function render(a){if(!a.skills)return;$('cov').textContent=a.skills.coverage+'%';$('tasks').textContent=a.learning.count;$('port').textContent=a.resume_agent.health+'%';$('ready').textContent=a.placement_agent.readiness+'%';const twin='<b>'+escapeHtml(a.digital_twin.current||'No skills yet')+'</b> → <b>'+escapeHtml(a.digital_twin.target)+'</b><p>Priority gaps: '+escapeHtml(a.digital_twin.gaps.join(', ')||'None')+'</p><p>Next actions: '+escapeHtml(a.digital_twin.next_actions.join(', ')||'Maintain momentum')+'</p>';['twinHome','twinPage'].forEach(id=>$(id).innerHTML=twin);const graph=a.skills.graph.map(x=>'<span class="node '+x.status+'">'+escapeHtml(x.skill)+(x.depends_on?' ← '+escapeHtml(x.depends_on):'')+'</span>').join('');['graphHome','skillPage'].forEach(id=>$(id).innerHTML=graph);const roadmap=a.learning.tasks.map(t=>'<div class=task><b>Day '+t.day+': '+escapeHtml(t.skill)+'</b> <small>'+t.priority+'</small><br>'+escapeHtml(t.task)+'</div>').join('');['roadmapHome','learningPage'].forEach(id=>$(id).innerHTML=roadmap);$('insight').textContent=a.summary;$('explain').innerHTML='<h3>Why this readiness result?</h3>'+a.explainability.map(x=>'<div class=result><b>'+escapeHtml(x.factor)+': '+x.value+'%</b><p>'+escapeHtml(x.reason)+'</p></div>').join('')}
async function jobAnalyze(i,o){try{let d=await api('/api/job',{method:'POST',body:JSON.stringify({job_text:$(i).value})}),r=d.result;$(o).innerHTML='<div class=result><b>Match: '+r.match+'%</b><p>Matched: '+escapeHtml(r.matched.join(', ')||'None')+'</p><p>Gaps: '+escapeHtml(r.gaps.join(', ')||'None')+'</p><p>Detected: '+escapeHtml(r.required.join(', '))+'</p><p>'+escapeHtml(r.recommendation)+'</p></div>'}catch(e){$(o).textContent=e.message}}
async function simulate(){try{let d=await api('/api/simulate',{method:'POST',body:JSON.stringify({target_role:$('simRole').value,added_skills:$('simSkills').value})}),s=d.scenario;$('simres').innerHTML='<div class=result><b>'+escapeHtml(s.target)+'</b><p>Coverage: '+s.coverage_before+'% → <b>'+s.coverage_after+'%</b></p><p>Added: '+escapeHtml(s.added.join(', ')||'None')+'</p><p>Remaining gaps: '+escapeHtml(s.gaps.join(', ')||'None')+'</p></div>'}catch(e){$('simres').textContent=e.message}}
async function startInterview(){try{let d=await api('/api/interview/start',{method:'POST',body:JSON.stringify({role:$('intRole').value,difficulty:$('intDifficulty').value})});window.currentInterview=d;let h='<h3>'+escapeHtml(d.role)+' — '+escapeHtml(d.difficulty)+'</h3>';d.questions.forEach((q,i)=>h+='<div class=question><b>Q'+(i+1)+'. '+escapeHtml(q)+'</b><textarea class=intAnswer data-i='+i+' placeholder="Write your answer..."></textarea></div>');h+='<button onclick=submitInterview()>Submit Interview</button><div id=intResult></div>';$('interviewBox').innerHTML=h}catch(e){$('interviewBox').textContent=e.message}}
async function submitInterview(){let answers=[...document.querySelectorAll('.intAnswer')].map(x=>x.value);try{let d=await api('/api/interview/submit',{method:'POST',body:JSON.stringify({role:window.currentInterview.role,difficulty:window.currentInterview.difficulty,questions:window.currentInterview.questions,answers})});$('intResult').innerHTML='<div class=result><b>Practice score: '+d.result.score+'%</b><p>'+escapeHtml(d.result.feedback)+'</p>'+((d.result.rubric||[]).map((r,i)=>'<div class=result><b>Answer '+(i+1)+': '+r.score+'%</b><p>'+escapeHtml(r.feedback)+'</p><small>Detail '+r.criteria.answer_detail+'/25 · Example '+r.criteria.specific_example+'/25 · Reasoning '+r.criteria.technical_reasoning+'/25 · Outcome '+r.criteria.outcome_or_learning+'/25</small></div>').join(''))+'<p>Improvements: '+escapeHtml(d.result.improvements.join(', '))+'</p><small>'+escapeHtml(d.result.disclaimer||'Practice feedback only.')+'</small></div>'; loadInterviews()}catch(e){$('intResult').textContent=e.message}}
async function loadInterviews(){try{let d=await api('/api/dashboard');$('interviewHistory').innerHTML='<h3>Recent Interviews</h3>'+d.interviews.map(x=>'<div class=result>'+escapeHtml(x.role)+' — '+x.score+'% — '+escapeHtml(x.created_at)+'</div>').join('')}catch(e){}}
async function addApplication(){try{await api('/api/applications',{method:'POST',body:JSON.stringify({company:$('appCompany').value,role:$('appRole').value,status:$('appStatus').value,match_score:$('appScore').value,notes:$('appNotes').value})});await loadApplications()}catch(e){alert(e.message)}}
async function loadApplications(){try{let d=await api('/api/applications');const html=d.applications.map(x=>'<div class=result><b>'+escapeHtml(x.company)+' — '+escapeHtml(x.role)+'</b><p>Status: '+escapeHtml(x.status)+' | Match: '+x.match_score+'%</p><p>'+escapeHtml(x.notes||'')+'</p><button onclick=editApplication('+Number(x.id)+')>Edit</button><button onclick=deleteApplication('+Number(x.id)+')>Delete</button></div>').join('');$('applicationList').innerHTML=html;$('applicationPage').innerHTML=html||'<p>No applications tracked yet.</p>'}catch(e){}}
async function editApplication(id){try{const d=await api('/api/applications');const x=d.applications.find(a=>a.id===id);if(!x)return;const company=prompt('Company',x.company);if(company===null)return;const role=prompt('Role',x.role);if(role===null)return;const status=prompt('Status: Interested, Applied, Screening, Assessment, Interview, Offer, Rejected, Withdrawn',x.status);if(status===null)return;const match_score=prompt('Match score (0-100)',x.match_score);if(match_score===null)return;const notes=prompt('Notes',x.notes||'');if(notes===null)return;await api('/api/applications/'+id,{method:'PUT',body:JSON.stringify({company,role,status,match_score,notes})});await loadApplications()}catch(e){alert(e.message)}}
async function deleteApplication(id){if(!confirm('Delete this application record?'))return;try{await api('/api/applications/'+id,{method:'DELETE'});await loadApplications()}catch(e){alert(e.message)}}
async function addProgress(){try{await api('/api/progress',{method:'POST',body:JSON.stringify({skill:$('progressSkill').value,score:$('progressScore').value})});$('progressMsg').textContent='Progress recorded.'}catch(e){$('progressMsg').textContent=e.message}}
async function loadDashboard(){try{let d=await api('/api/dashboard');const html=d.activity.map(x=>'<div class=result><b>'+escapeHtml(x.agent)+'</b> — '+escapeHtml(x.action)+' — '+escapeHtml(x.status)+'<small>'+escapeHtml(x.created_at)+'</small></div>').join('');$('activityHome').innerHTML=html||'No agent runs yet.';$('agentsPage').innerHTML=html||'No agent runs yet.'}catch(e){$('agentsPage').textContent=e.message}}
function appendChatMessage(role,message){const el=document.createElement('div');el.className=role==='user'?'usr':'bot';el.textContent=String(message??'');$('chatlog').appendChild(el);$('chatlog').scrollTop=$('chatlog').scrollHeight}
async function loadChatHistory(){try{const d=await api('/api/chat/history');$('chatlog').innerHTML='';(d.messages||[]).forEach(x=>appendChatMessage(x.role,x.message))}catch(e){}}
async function chat(){const input=$('chatInput'),button=$('chatSendButton'),status=$('chatStatus');let m=input.value.trim();if(!m||button.disabled)return;appendChatMessage('user',m);input.value='';button.disabled=true;button.textContent='…';status.textContent='Thinking…';try{let d=await api('/api/chat',{method:'POST',body:JSON.stringify({message:m})});appendChatMessage('assistant',d.answer);status.textContent=d.mode==='contextual_fallback'?'Quick personalized answer (local AI is busy or unavailable).':''}catch(e){appendChatMessage('assistant','I could not reach the chat service. Please try again. ('+e.message+')');status.textContent='Could not connect'}finally{button.disabled=false;button.textContent='Send';input.focus()}}
async function loadResume(){try{const d=await api('/api/resume');if(d.resume)renderResume(d.resume.filename,d.resume.analysis,d.resume.updated_at)}catch(e){}}
function renderResume(filename,a,updated){$('resumeResult').innerHTML='<div class=result><b>'+escapeHtml(filename)+' — Resume structure score: '+a.score+'%</b><p>Extracted word count: '+a.word_count+' · Updated: '+escapeHtml(updated||'just now')+'</p><div>'+Object.entries(a.sections||{}).map(([k,v])=>'<span class="node '+(v?'matched':'gap')+'">'+escapeHtml(k)+': '+(v?'Found':'Missing')+'</span>').join('')+'</div><h3>Suggestions</h3><ul>'+a.suggestions.map(x=>'<li>'+escapeHtml(x)+'</li>').join('')+'</ul><small>'+escapeHtml(a.disclaimer)+'</small></div>'}
const resumeForm=$('resumeForm');if(resumeForm)resumeForm.addEventListener('submit',async e=>{e.preventDefault();const box=$('resumeResult');box.textContent='Extracting resume text locally...';try{const fd=new FormData();fd.append('resume',$('resumeFile').files[0]);const d=await api('/api/resume',{method:'POST',body:fd});renderResume(d.filename,d.analysis,'just now')}catch(err){box.textContent=err.message}});
async function feedback(r){try{await api('/api/feedback',{method:'POST',body:JSON.stringify({rating:r,context:'AI Insight'})});$('insight').textContent+=' Feedback recorded.'}catch(e){}}
async function evaluate(){try{let d=await api('/api/evaluation');$('eval').innerHTML=Object.entries(d.metrics).map(x=>'<div class=result><b>'+escapeHtml(x[0])+'</b>: '+x[1]+'</div>').join('')}catch(e){$('eval').textContent=e.message}}
async function report(){try{let d=await api('/api/report');$('rep').textContent=JSON.stringify(d.report,null,2)}catch(e){$('rep').textContent=e.message}}
function escapeHtml(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
document.querySelectorAll('main>section').forEach(s=>s.style.display=s.id==='command'?'block':'none');
document.querySelectorAll('aside button').forEach(b=>b.onclick=()=>{document.querySelectorAll('main>section').forEach(s=>s.style.display='none');const target=$(b.dataset.s);if(target)target.style.display='block';document.querySelectorAll('aside button').forEach(x=>x.classList.remove('active'));b.classList.add('active');if(b.dataset.s==='agents')loadDashboard();if(b.dataset.s==='applications')loadApplications();if(b.dataset.s==='interview')loadInterviews();if(b.dataset.s==='evaluation')evaluate();if(b.dataset.s==='reports')report();if(b.dataset.s==='learning')loadLearningTasks();if(b.dataset.s==='resume')loadResume()});document.querySelector('aside button').classList.add('active');load().catch(e=>{if($('authmsg'))$('authmsg').textContent='Connect by creating an account or logging in.'});

function escapeLearningText(value){
  return String(value ?? '').replace(/[&<>"']/g,c=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));
}

async function loadLearningTasks(){
  const box = $('learningPage');
  if(!box) return;

  try {
    const d = await api('/api/learning-tasks');
    const tasks = d.tasks || [];

    if(!tasks.length){
      box.innerHTML = '<p>No learning roadmap yet. Generate one from your career profile.</p><button id="generateLearningBtn">Generate My Learning Roadmap</button>';
      $('generateLearningBtn').onclick = generateLearningTasks;
      return;
    }

    box.innerHTML = tasks.map(t => `
      <article style="border:1px solid #ddd;border-radius:8px;padding:12px;margin:10px 0">
        <h3>Week ${escapeLearningText(t.week_number)}: ${escapeLearningText(t.skill)}</h3>
        <p>${escapeLearningText(t.task)}</p>
        <p>Priority: ${escapeLearningText(t.priority)}</p>
        <label>Status:
          <select data-task-status="${Number(t.id)}">
            <option value="Not Started" ${t.status==='Not Started'?'selected':''}>Not Started</option>
            <option value="In Progress" ${t.status==='In Progress'?'selected':''}>In Progress</option>
            <option value="Completed" ${t.status==='Completed'?'selected':''}>Completed</option>
          </select>
        </label>
      </article>
    `).join('');

    box.querySelectorAll('[data-task-status]').forEach(el => {
      el.onchange = async () => {
        try {
          await api('/api/learning-tasks/' + el.dataset.taskStatus + '/status', {
            method:'POST',
            body:JSON.stringify({status:el.value})
          });
          await loadLearningTasks();
        } catch(e) {
          alert(e.message);
          await loadLearningTasks();
        }
      };
    });
  } catch(e) {
    box.textContent = 'Could not load learning tasks: ' + e.message;
  }
}

async function generateLearningTasks(){
  const box = $('learningPage');
  if(box) box.textContent = 'Generating your personalized learning roadmap...';

  try {
    await api('/api/learning-tasks/generate', {
      method:'POST',
      body:JSON.stringify({})
    });
    await loadLearningTasks();
  } catch(e) {
    if(box) box.textContent = 'Could not generate roadmap: ' + e.message;
  }
}
