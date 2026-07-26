// Ghost Capture v3 — Text-Diff Approach
// No DOM selectors, no class names. Just watch text changes.
// ========================================================

var CONFIG = {
  pollMs: 2000,
  minTextLen: 10
};

var lastText = "";
var buffered = [];
var sessionId = "web-" + Date.now() + "-" + Math.random().toString(36).slice(2,8);
var isRunning = true;

function getVisibleText() {
  // Get ALL visible text from the page body
  var body = document.body;
  if (!body) return "";
  var text = body.innerText || "";
  // Normalize whitespace
  return text.replace(/\s+/g, " ").trim();
}

function findNewContent(oldText, newText) {
  if (!oldText) return [];
  
  // Simple diff: find text that exists in new but not old
  // Split into reasonable chunks
  var oldChunks = oldText.split(/\n+/).filter(function(c){return c.trim().length > CONFIG.minTextLen;});
  var newChunks = newText.split(/\n+/).filter(function(c){return c.trim().length > CONFIG.minTextLen;});
  
  var results = [];
  var oldSet = {};
  for (var i = 0; i < oldChunks.length; i++) {
    oldSet[oldChunks[i].slice(0, 60)] = true;
  }
  
  for (var i = 0; i < newChunks.length; i++) {
    var key = newChunks[i].slice(0, 60);
    if (!oldSet[key]) {
      // This is new content!
      var text = newChunks[i].trim();
      if (text.length > CONFIG.minTextLen) {
        results.push(text);
      }
    }
  }
  
  return results;
}

function sendCapture(contents) {
  if (!contents || contents.length === 0) return;
  
  var messages = [];
  for (var i = 0; i < contents.length; i++) {
    // Heuristic: short queries are likely user, long responses are assistant
    // This is imperfect but works for most chat patterns
    var isUser = contents[i].length < 100 || contents[i].endsWith("?") || contents[i].endsWith("？");
    messages.push({
      role: isUser ? "user" : "assistant",
      content: contents[i],
      timestamp: Date.now()
    });
  }
  
  fetch("http://localhost:18080/v1/doubao/capture", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      session_id: sessionId,
      bot_id: "doubao_web",
      captured_at: Math.floor(Date.now()/1000),
      messages: messages
    })
  }).then(function(r){return r.json().catch(function(){return {};});})
    .then(function(d){console.log("[GC] Sent",messages.length,"msgs:",d.status||"ok");})
    .catch(function(err){
      console.log("[GC] GW down:", err.message);
      buffered = buffered.concat(contents);
    });
}

function flush() {
  if (buffered.length === 0) return;
  var batch = buffered.splice(0);
  sendCapture(batch.map(function(t){return {role:"user",content:t,timestamp:Date.now()};}));
}

function checkForChanges() {
  if (!isRunning) return;
  flush();
  
  var currentText = getVisibleText();
  if (!currentText || currentText.length < 50) return;
  
  var newContent = findNewContent(lastText, currentText);
  if (newContent.length > 0) {
    console.log("[GC] +" + newContent.length + " new text chunks");
    sendCapture(newContent);
  }
  
  lastText = currentText;
}

// Start
console.log("[Ghost Capture] v3 starting - text-diff mode");
setTimeout(function() { lastText = getVisibleText(); }, 500);
setInterval(checkForChanges, CONFIG.pollMs);

// Also observe DOM changes for immediate capture
if (document.body) {
  var obs = new MutationObserver(function() {
    clearTimeout(window._gc_timer);
    window._gc_timer = setTimeout(checkForChanges, 300);
  });
  obs.observe(document.body, { childList: true, subtree: true, characterData: true });
}

// Notify popup
chrome.runtime.sendMessage({type:"CONTENT_LOADED",url:location.href}).catch(function(){});
