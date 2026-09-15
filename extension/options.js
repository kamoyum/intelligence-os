(async()=>{
  await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}).catch(()=>{});
  let x=await chrome.storage.local.get(['coreUrl','apiToken','allowExternalLlm','connectionMode']);
  core.value=x.coreUrl||'http://127.0.0.1:8765';
  token.value=x.apiToken||'';
  allowExternal.checked=Boolean(x.allowExternalLlm);
  mode.value=x.connectionMode||'auto';
})();
save.onclick=async()=>{
  await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}).catch(()=>{});
  await chrome.storage.local.set({coreUrl:core.value.replace(/\/$/,''),apiToken:token.value.trim(),allowExternalLlm:Boolean(allowExternal.checked),connectionMode:mode.value});
  msg.textContent=' 保存しました';setTimeout(()=>msg.textContent='',1500)
};
testNative.onclick=()=>chrome.runtime.sendMessage({type:'TEST_NATIVE'},res=>{
  if(res?.ok){nativeMsg.textContent=' 接続OK';nativeMsg.className='ok'}else{nativeMsg.textContent=' 接続不可: '+(res?.error||'unknown');nativeMsg.className='bad'}
});
