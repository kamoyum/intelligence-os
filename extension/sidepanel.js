const esc=s=>String(s??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[m]));

async function call(path, options={}) {
  return new Promise((resolve,reject)=>chrome.runtime.sendMessage({type:'CORE_REQUEST',path,options},res=>{
    if(chrome.runtime.lastError) return reject(chrome.runtime.lastError);
    if(res?.error) return reject(new Error(res.error));
    if(!res?.ok) return reject(new Error(res?.data?.detail || res?.error || `HTTP ${res?.status}`));
    resolve({...res.data,_transport:res.transport});
  }));
}

async function active(){
  let [t]=await chrome.tabs.query({active:true,currentWindow:true});
  page.textContent=t?.title||'—';
  url.textContent=t?.url||'';
  return t;
}

async function health(){
  try{let j=await call('/api/health');status.textContent=`CORE ON · ${j._transport||'?'}`}
  catch{status.textContent='CORE OFF'}
}

async function loadAttention(){
  try{
    let a=await call('/api/attention/queue?limit=6');
    attention.innerHTML=a.map(x=>`<div class=mem><b>${esc(x.title)}</b><br><span class=muted>${esc(x.type||'item')} · attention ${Math.round((x.score??0)*100)}% · ${(x.why||[]).map(esc).join(' / ')}</span></div>`).join('')||'今すぐ注意が必要な項目はありません';
  }catch(e){
    attention.innerHTML=`${esc(e.message)}<br><button class=secondary id=openOptions>設定を開く</button>`;
    document.getElementById('openOptions')?.addEventListener('click',()=>chrome.runtime.openOptionsPage());
  }
}

remember.onclick=async()=>{
  remember.textContent='記憶中…';
  chrome.runtime.sendMessage({type:'CAPTURE_ACTIVE'},res=>{
    remember.textContent=res?.error?'失敗':`記憶しました${res?.transport?' · '+res.transport:''}`;
    if(res?.error)answer.textContent=res.error;
    setTimeout(()=>remember.textContent='このページを記憶',1400);
    loadAttention();
  });
};

function feedbackButtons(taskId){
  if(!taskId) return '';
  return `<div class="feedback" style="margin-top:10px"><div class="muted">この応答は？</div>
    <button class="secondary fb" data-task="${taskId}" data-signal="helped_me_think">考える助けになった</button>
    <button class="secondary fb" data-task="${taskId}" data-signal="saved_repetitive_work">単純作業を減らせた</button>
    <button class="secondary fb" data-task="${taskId}" data-signal="caught_an_error">誤りを見つけた</button>
    <button class="secondary fb" data-task="${taskId}" data-signal="made_me_think_less">考えなくなりそう</button>
    <button class="secondary fb" data-task="${taskId}" data-signal="wrong_or_unsafe">誤り・危険を感じた</button>
  </div>`;
}

function bindFeedback(){
  document.querySelectorAll('.fb').forEach(btn=>btn.addEventListener('click',async()=>{
    const signal=btn.dataset.signal;
    const taskId=Number(btn.dataset.task);
    try{
      await call('/api/feedback',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({signal,task_id:taskId})});
      document.querySelectorAll('.fb').forEach(x=>x.disabled=true);
      btn.textContent='記録しました';
    }catch(e){btn.textContent='記録失敗: '+e.message}
  }));
}

ask.onclick=async()=>{
  answer.textContent='Thinking…';
  try{
    let t=await active();
    let cfg=await chrome.storage.local.get(['allowExternalLlm']);
    let prompt=cfg.allowExternalLlm?`現在のページ: ${t?.title||''}\n${t?.url||''}\n\n${q.value}`:q.value;
    let j=await call('/api/ask',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({
      query:prompt,
      allow_external_research:!!document.getElementById('allowResearch')?.checked,
      allow_external_reasoning:!!document.getElementById('allowReasoning')?.checked
    })});
    let research='';
    if(j.research){
      let src=(j.research.sources||[]).filter(x=>x.fetched).slice(0,3).map(x=>`<a href="${esc(x.url)}" target="_blank" style="color:#58a6ff">${esc(x.title)}</a>`).join('<br>');
      research=`<div class="muted" style="margin-top:8px"><b>Current Web Research</b>: ${j.research.sources_fetched||0} sources fetched<br>${src}</div>`;
    }else if(j.research_error){
      research=`<div class="muted" style="margin-top:8px">Research: ${esc(j.research_error)}</div>`;
    }
    const humanFirst=j.executive_plan?.human_first_prompt?`<br><b>Human-first:</b> ${esc(j.executive_plan.human_first_prompt)}`:'';
    answer.innerHTML=`${esc(j.answer).replace(/\n/g,'<br>')}${research}<div class=muted style="margin-top:8px">
      Executive: ${esc(j.executive_plan?.autonomy||'?')} · Cognitive: ${esc(j.executive_plan?.cognitive_mode||'?')} · Risk: ${esc(j.executive_plan?.risk||'?')}<br>
      Skills: ${(j.executive_plan?.skills||[]).map(esc).join(' / ')||'none'}<br>
      Query safety: ${esc(j.executive_plan?.query_safety?.level||'safe')} · Evidence: ${esc(j.executive_plan?.evidence_requirement||'none')}<br>
      Human role: ${esc(j.executive_plan?.human_role||'')}${humanFirst}<br>
      Transport: ${esc(j._transport||'?')} · Eval: ${esc(j.eval.method)} · grounded ${j.eval.groundedness} / relevance ${j.eval.relevance}<br>
      Memory: ${(j.memories||[]).map(x=>esc(x.title)).join(' / ')||'none'}<br>
      External memory shared: ${j.privacy?.shared_with_external_llm ?? 'n/a'} / withheld: ${j.privacy?.withheld_from_external_llm ?? 'n/a'}
    </div>${feedbackButtons(j.task_id)}`;
    bindFeedback();
    loadAttention();
  }catch(e){answer.textContent='Core error: '+e.message}
};

consoleBtn.onclick=()=>chrome.tabs.create({url:'http://127.0.0.1:8765/console'});
settingsBtn.onclick=()=>chrome.runtime.openOptionsPage();
active();health();loadAttention();setInterval(health,15000);
