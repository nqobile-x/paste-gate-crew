let toast = null;

function showToast(msg, type = 'info') {
  if (toast) toast.remove();
  toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed;bottom:24px;right:24px;z-index:2147483647;
    background:${type==='error'?'#3a1a1a':type==='success'?'#1a2a1a':'#1c1812'};
    color:${type==='error'?'#f87171':type==='success'?'#86efac':'#e8dccf'};
    border:1px solid ${type==='error'?'rgba(248,113,113,.3)':type==='success'?'rgba(134,239,172,.3)':'rgba(201,169,110,.22)'};
    border-radius:12px;padding:12px 18px;font-family:system-ui,sans-serif;
    font-size:13px;line-height:1.5;max-width:320px;
    box-shadow:0 8px 32px rgba(0,0,0,.5);
    animation:pgSlide .25s ease;
  `;
  if (!document.getElementById('pg-anim')) {
    const style = document.createElement('style');
    style.id = 'pg-anim';
    style.textContent = `@keyframes pgSlide{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}`;
    document.head.appendChild(style);
  }
  toast.innerHTML = msg;
  document.body.appendChild(toast);
  setTimeout(() => { if (toast) { toast.style.opacity='0'; toast.style.transition='opacity .3s'; setTimeout(()=>toast?.remove(),300); }}, 4000);
}

function replaceSelection(text) {
  const active = document.activeElement;
  if (active && (active.tagName === 'TEXTAREA' || (active.tagName === 'INPUT' && active.type === 'text'))) {
    const start = active.selectionStart;
    const end = active.selectionEnd;
    active.value = active.value.slice(0, start) + text + active.value.slice(end);
    active.selectionStart = active.selectionEnd = start + text.length;
    active.dispatchEvent(new Event('input', {bubbles: true}));
    return true;
  }
  // contenteditable
  const sel = window.getSelection();
  if (sel && sel.rangeCount) {
    sel.deleteFromDocument();
    sel.getRangeAt(0).insertNode(document.createTextNode(text));
    sel.collapseToEnd();
    return true;
  }
  return false;
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'SCRUB_START') {
    showToast(`
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:14px;height:14px;border:2px solid #c9a96e;border-top-color:transparent;border-radius:50%;animation:pgSpin 0.7s linear infinite;flex-shrink:0;"></div>
        <span><strong style="color:#c9a96e">Aria</strong> is scrubbing…</span>
      </div>
      <style>@keyframes pgSpin{to{transform:rotate(360deg)}}</style>
    `);
  }
  if (msg.type === 'SCRUB_DONE') {
    replaceSelection(msg.scrubbed);
    const riskColor = msg.risk==='high'?'#f87171':msg.risk==='medium'?'#fbbf24':'#86efac';
    showToast(`
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#c9a96e" stroke-width="2.5" stroke-linecap="round"><path d="M12 2L4 6v6c0 5.25 3.5 10 8 12 4.5-2 8-6.75 8-12V6L12 2z"/><polyline points="9 12 11 14 15 10"/></svg>
        <strong style="color:#c9a96e">Scrub complete</strong>
        <span style="margin-left:auto;font-size:10px;font-family:monospace;background:${riskColor}22;color:${riskColor};padding:2px 6px;border-radius:4px;border:1px solid ${riskColor}44">${msg.risk.toUpperCase()}</span>
      </div>
      <div style="font-size:12px;color:#9a8a78">${msg.entities} entit${msg.entities!==1?'ies':'y'} redacted · ${msg.session_key}</div>
    `, 'success');
  }
  if (msg.type === 'SCRUB_ERROR') {
    showToast(`<strong style="color:#f87171">Error:</strong> ${msg.message}`, 'error');
  }
});
