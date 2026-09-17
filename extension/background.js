const API = 'https://paste-gate-crew.onrender.com/scrub';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'scrub-selection',
    title: 'Scrub with Aria',
    contexts: ['selection']
  });
});

// right-click scrub from any page
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

// popup scrub — runs in background so popup closing doesn't kill the request
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== 'SCRUB_POPUP') return false;
  fetch(API, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: msg.text})
  })
  .then(r => r.json())
  .then(data => sendResponse({ok: true, data}))
  .catch(err => sendResponse({ok: false, error: err.message}));
  return true; // keeps the message channel open for async response
});
