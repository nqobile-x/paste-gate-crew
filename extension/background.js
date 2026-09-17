const API = 'https://paste-gate-crew.onrender.com/scrub';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'scrub-selection',
    title: 'Scrub with Aria',
    contexts: ['selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== 'scrub-selection') return;
  chrome.tabs.sendMessage(tab.id, {type: 'SCRUB_START'});

  fetch(API, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: info.selectionText})
  })
  .then(r => r.json())
  .then(data => {
    chrome.tabs.sendMessage(tab.id, {
      type: 'SCRUB_DONE',
      scrubbed: data.scrubbed_text,
      entities: data.entities_found,
      risk: data.risk_level,
      session_key: data.session_key
    });
  })
  .catch(err => {
    chrome.tabs.sendMessage(tab.id, {type: 'SCRUB_ERROR', message: err.message});
  });
});
