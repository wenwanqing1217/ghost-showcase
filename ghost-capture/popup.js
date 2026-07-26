// Ghost Capture — Popup Logic
const GATEWAY_URL = 'http://localhost:18080';

async function checkStatus() {
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  
  try {
    const resp = await fetch(GATEWAY_URL + '/health');
    const data = await resp.json();
    if (data.success) {
      dot.className = 'dot green';
      text.textContent = 'Gateway 已连接';
    } else {
      dot.className = 'dot yellow';
      text.textContent = 'Gateway 异常';
    }
  } catch {
    dot.className = 'dot red';
    text.textContent = 'Gateway 未连接';
  }
}

async function loadStats() {
  try {
    const resp = await fetch(GATEWAY_URL + '/v1/dashboard');
    const data = await resp.json();
    if (data.success && data.data) {
      document.getElementById('msgCount').textContent = data.data.identity?.state === 'awake' ? '✓' : '?';
    }
  } catch {}
}

document.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  loadStats();
  document.getElementById('metaInfo').textContent = 'Ghost v2.0 | Localhost:18080';
});

document.getElementById('openDoubao').addEventListener('click', () => {
  chrome.tabs.create({ url: 'https://www.doubao.com' });
});

document.getElementById('openGhost').addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:8000' });
});
