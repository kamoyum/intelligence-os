const HOST_NAME = 'com.intelligenceos.native';
const DEFAULT_CORE = 'http://127.0.0.1:8765';

async function settings() {
  const x = await chrome.storage.local.get(['coreUrl','apiToken','allowExternalLlm','connectionMode']);
  return {
    core: x.coreUrl || DEFAULT_CORE,
    token: x.apiToken || '',
    allowExternalLlm: Boolean(x.allowExternalLlm),
    mode: x.connectionMode || 'auto'
  };
}

async function nativeRequest(path, options={}) {
  const msg = {
    action: 'request',
    path,
    method: (options.method || 'GET').toUpperCase(),
    body: options.body ? JSON.parse(options.body) : undefined
  };
  return await chrome.runtime.sendNativeMessage(HOST_NAME, msg);
}

async function legacyHttp(path, options={}) {
  const {core, token} = await settings();
  if (!token) throw new Error('Legacy HTTP token is not configured. Use Native Messaging or set the token in Options.');
  const headers = {...(options.headers||{}), 'Authorization': `Bearer ${token}`};
  const r = await fetch(core + path, {...options, headers});
  const data = await r.json().catch(()=>({}));
  return {ok:r.ok,status:r.status,data};
}

async function coreRequest(path, options={}) {
  const cfg = await settings();
  if (cfg.mode !== 'http') {
    try {
      const res = await nativeRequest(path, options);
      if (res && (res.ok || res.status)) return {...res, transport:'native'};
    } catch (e) {
      if (cfg.mode === 'native') throw new Error('Native bridge unavailable: ' + (e?.message || e));
    }
  }
  const res = await legacyHttp(path, options);
  return {...res, transport:'http'};
}

chrome.runtime.onInstalled.addListener(async () => {
  await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}).catch(()=>{});
  await chrome.storage.local.set({connectionMode:(await chrome.storage.local.get('connectionMode')).connectionMode || 'auto'});
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(console.error);
  chrome.contextMenus.create({ id: 'ios-save', title: 'Intelligence OSに記憶', contexts: ['page', 'selection', 'link'] });
  chrome.contextMenus.create({ id: 'ios-open', title: 'Intelligence OSで考える', contexts: ['page', 'selection'] });
});
chrome.runtime.onStartup.addListener(()=>chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}).catch(()=>{}));

async function captureTab(tab, selectionText='') {
  const [{result}] = await chrome.scripting.executeScript({
    target: {tabId: tab.id},
    func: () => ({ title: document.title, url: location.href, text: (window.getSelection()?.toString() || document.body?.innerText || '').slice(0, 50000) })
  });
  const content = selectionText || result.text || result.title;
  const {allowExternalLlm} = await settings();
  const res = await coreRequest('/api/capture', {
    method:'POST',
    headers:{'content-type':'application/json'},
    body:JSON.stringify({
      title:result.title,url:result.url,content,source_type:'browser',source_key:result.url,
      tags:['extension'],sensitivity:'private',allow_external_llm:allowExternalLlm
    })
  });
  if (!res.ok) throw new Error(res?.data?.detail || res?.error || `HTTP ${res.status}`);
  return {...res.data, transport:res.transport};
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab?.id) return;
  try {
    if (info.menuItemId === 'ios-save') await captureTab(tab, info.selectionText || '');
    if (info.menuItemId === 'ios-open') await chrome.sidePanel.open({tabId: tab.id});
  } catch (e) { console.error(e); }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async()=>{
    if (msg.type === 'CAPTURE_ACTIVE') {
      const [tab] = await chrome.tabs.query({active:true,currentWindow:true});
      sendResponse(await captureTab(tab, msg.selection || ''));
      return;
    }
    if (msg.type === 'CORE_REQUEST') {
      sendResponse(await coreRequest(msg.path, msg.options || {}));
      return;
    }
    if (msg.type === 'GET_SETTINGS') { sendResponse(await settings()); return; }
    if (msg.type === 'TEST_NATIVE') {
      try {
        const r = await chrome.runtime.sendNativeMessage(HOST_NAME,{action:'ping'});
        sendResponse(r || {ok:false});
      } catch(e) { sendResponse({ok:false,error:String(e?.message||e)}); }
      return;
    }
  })().catch(e=>sendResponse({error:String(e.message || e)}));
  return true;
});
