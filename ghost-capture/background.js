// Ghost Capture — Background Service Worker
// 后台处理消息转发、连接状态管理
const GATEWAY_URL = 'http://localhost:18080/v1/doubao/capture';
let connectionStatus = 'unknown';

// 检查 Gateway 连接
async function checkConnection() {
  try {
    const resp = await fetch(GATEWAY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: 'ping', messages: [] })
    });
    connectionStatus = resp.ok ? 'connected' : 'error';
  } catch {
    connectionStatus = 'disconnected';
  }
  return connectionStatus;
}

// 定时检查连接
chrome.alarms.create('healthCheck', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'healthCheck') checkConnection();
});

// 处理来自 content script 的消息
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'CONTENT_LOADED') {
    checkConnection().then(status => {
      console.log('[Ghost Capture] Page loaded, Gateway:', status);
    });
  }
  if (msg.type === 'MESSAGES_UPDATED') {
    // 可以在这里做批量处理
  }
  sendResponse({ status: 'ok' });
});

// 安装时打开 popup 提示
chrome.runtime.onInstalled.addListener(() => {
  console.log('[Ghost Capture] Installed');
  checkConnection();
});
