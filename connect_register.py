"""Connect Ghost.html login to flow/api registration (SMS + Face + DID)."""
import re

FILE = r'D:\MW\Ghost.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File size: {len(content)} chars")

# 1. Add FLOW_API constant after ALPHAID_API
old_vars = "  var ALPHAID_API = 'http://localhost:8000';"
new_vars = """  var ALPHAID_API = 'http://localhost:8000';
  var FLOW_API = 'http://localhost:3001';  // flow/api: 注册/短信/人脸/DID"""
content = content.replace(old_vars, new_vars)

# 2. Replace face-auth-modal HTML with registration form
# Find the modal div
modal_start = content.find('<div class="face-auth-overlay"')
if modal_start < 0:
    print("ERROR: face-auth-overlay not found")
else:
    # Find the end of the modal (next </div> after modal content)
    # We need to find the matching closing div
    depth = 0
    i = modal_start
    while i < len(content):
        if content[i:i+4] == '<div':
            depth += 1
        elif content[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                modal_end = i + 6
                break
        i += 1
    else:
        modal_end = len(content)

    print(f"Modal: {modal_start}-{modal_end}")

    new_modal = '''<div class="face-auth-overlay" id="face-auth-modal">
  <div class="face-auth-modal">
    <button class="absolute top-4 right-4 text-slate-500 hover:text-white transition z-10" onclick="closeFaceAuth()" style="background:none;border:none;font-size:24px;cursor:pointer">&times;</button>

    <!-- Step 1: 手机号 -->
    <div id="reg-step-phone">
      <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-4">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
      </div>
      <h3 class="text-xl font-bold text-white mb-2">手机验证</h3>
      <p class="text-sm text-slate-400 mb-6">输入手机号，获取验证码</p>
      <input type="tel" id="reg-phone" placeholder="13800138000" maxlength="11"
        class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-center text-lg tracking-widest focus:outline-none focus:border-violet-500 mb-4">
      <div id="reg-sms-demo-code" class="text-xs text-amber-400 mb-3 hidden"></div>
      <button onclick="sendSMS()" id="reg-btn-send" class="btn-primary w-full py-3 rounded-xl text-white font-semibold">获取验证码</button>
    </div>

    <!-- Step 2: 验证码 -->
    <div id="reg-step-code" class="hidden">
      <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mb-4">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
      </div>
      <h3 class="text-xl font-bold text-white mb-2">输入验证码</h3>
      <p class="text-sm text-slate-400 mb-6">已发送至 <span id="reg-phone-display"></span></p>
      <input type="text" id="reg-code" placeholder="6位验证码" maxlength="6"
        class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-center text-2xl tracking-[0.5em] focus:outline-none focus:border-cyan-500 mb-4">
      <button onclick="verifySMS()" class="btn-primary w-full py-3 rounded-xl text-white font-semibold">验证</button>
      <button onclick="showRegStep(1)" class="text-sm text-slate-500 hover:text-white mt-3">返回修改手机号</button>
    </div>

    <!-- Step 3: 实名认证 -->
    <div id="reg-step-face" class="hidden">
      <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-4">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
      </div>
      <h3 class="text-xl font-bold text-white mb-2">实名认证</h3>
      <p class="text-sm text-slate-400 mb-4">填写真实姓名和身份证号，跳转支付宝完成刷脸</p>
      <input type="text" id="reg-name" placeholder="真实姓名"
        class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-amber-500 mb-3">
      <input type="text" id="reg-idno" placeholder="身份证号" maxlength="18"
        class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-amber-500 mb-4">
      <button onclick="startFaceVerify()" id="reg-btn-face" class="btn-primary w-full py-3 rounded-xl text-white font-semibold">开始实名认证</button>
      <div id="reg-face-status" class="text-xs text-slate-500 mt-3"></div>
    </div>

    <!-- Step 4: 完成 -->
    <div id="reg-step-done" class="hidden">
      <div class="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-emerald-400 to-green-600 flex items-center justify-center mb-4">
        <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
      </div>
      <h3 class="text-xl font-bold text-white mb-2">注册成功</h3>
      <p class="text-sm text-slate-400 mb-2">你的数字身份已创建</p>
      <div class="bg-white/5 rounded-xl px-4 py-3 mb-4">
        <div class="text-xs text-slate-500 mb-1">DID</div>
        <div class="text-sm text-emerald-400 font-mono break-all" id="reg-did-display"></div>
      </div>
      <div class="text-xs text-slate-500" id="reg-alphaid-display"></div>
    </div>
  </div>
</div>'''

    content = content[:modal_start] + new_modal + content[modal_end:]
    print("Modal replaced")

# 3. Replace openFaceAuth function
old_func_start = content.find('window.openFaceAuth = function()')
if old_func_start < 0:
    print("ERROR: openFaceAuth not found")
else:
    # Find the end of the function (next function or closing brace at same level)
    brace_depth = 0
    i = old_func_start
    started = False
    while i < len(content):
        if content[i] == '{':
            brace_depth += 1
            started = True
        elif content[i] == '}':
            brace_depth -= 1
            if started and brace_depth == 0:
                func_end = i + 1
                break
        i += 1
    else:
        func_end = len(content)

    print(f"openFaceAuth: {old_func_start}-{func_end}")

    new_func = '''window.openFaceAuth = function() {
  var modal = document.getElementById('face-auth-modal');
  if (!modal) return;
  modal.classList.add('active');
  showRegStep(1);
};

window.showRegStep = function(n) {
  for (var i = 1; i <= 4; i++) {
    var el = document.getElementById('reg-step-' + (i === 1 ? 'phone' : i === 2 ? 'code' : i === 3 ? 'face' : 'done'));
    if (el) el.classList.toggle('hidden', i !== n);
  }
};

window.sendSMS = function() {
  var phone = document.getElementById('reg-phone').value.trim();
  if (!/^1[3-9]\\d{9}$/.test(phone)) { alert('请输入正确的手机号'); return; }
  var btn = document.getElementById('reg-btn-send');
  btn.disabled = true; btn.textContent = '发送中...';
  fetch(FLOW_API + '/api/register/send-sms', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phone })
  }).then(function(r) { return r.json(); }).then(function(data) {
    if (data.success) {
      document.getElementById('reg-phone-display').textContent = phone.replace(/(\\d{3})\\d{4}(\\d{4})/, '$1****$2');
      if (data.demo) {
        var demoEl = document.getElementById('reg-sms-demo-code');
        demoEl.textContent = '演示模式，验证码: ' + data.demo;
        demoEl.classList.remove('hidden');
      }
      showRegStep(2);
    } else {
      alert(data.error || '发送失败');
    }
    btn.disabled = false; btn.textContent = '获取验证码';
  }).catch(function(e) {
    alert('网络错误: ' + e.message);
    btn.disabled = false; btn.textContent = '获取验证码';
  });
};

window.verifySMS = function() {
  var phone = document.getElementById('reg-phone').value.trim();
  var code = document.getElementById('reg-code').value.trim();
  if (!code) { alert('请输入验证码'); return; }
  fetch(FLOW_API + '/api/register/verify-sms', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phone, code: code })
  }).then(function(r) { return r.json(); }).then(function(data) {
    if (data.success) {
      showRegStep(3);
    } else {
      alert(data.error || '验证失败');
    }
  }).catch(function(e) { alert('网络错误: ' + e.message); });
};

window.startFaceVerify = function() {
  var phone = document.getElementById('reg-phone').value.trim();
  var name = document.getElementById('reg-name').value.trim();
  var idNo = document.getElementById('reg-idno').value.trim();
  if (!name) { alert('请输入真实姓名'); return; }
  if (!idNo) { alert('请输入身份证号'); return; }
  var btn = document.getElementById('reg-btn-face');
  var status = document.getElementById('reg-face-status');
  btn.disabled = true; btn.textContent = '认证中...';
  status.textContent = '正在初始化支付宝认证...';

  fetch(FLOW_API + '/api/register/face-verify', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phone, name: name, idNo: idNo })
  }).then(function(r) { return r.json(); }).then(function(data) {
    if (!data.success) {
      status.textContent = '认证失败: ' + (data.error || '未知错误');
      btn.disabled = false; btn.textContent = '开始实名认证';
      return;
    }
    if (data.demo) {
      // 演示模式：直接通过
      status.textContent = '实名认证通过（演示模式）';
      setTimeout(function() { generateDID(phone); }, 800);
    } else {
      // 生产模式：轮询等待用户在支付宝 App 完成刷脸
      status.textContent = '请在支付宝 App 完成刷脸...';
      var certifyId = data.certifyId;
      if (data.qrUrl) {
        status.innerHTML = '请在支付宝 App 完成刷脸<br><a href="' + data.qrUrl + '" target="_blank" class="text-violet-400 underline">点击打开</a>';
      }
      // 轮询结果
      var pollCount = 0;
      var poll = setInterval(function() {
        pollCount++;
        if (pollCount > 30) { clearInterval(poll); status.textContent = '认证超时'; btn.disabled = false; btn.textContent = '重试'; return; }
        fetch(FLOW_API + '/api/register/face-query', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ certifyId: certifyId })
        }).then(function(r) { return r.json(); }).then(function(q) {
          if (q.passed === true) {
            clearInterval(poll);
            status.textContent = '实名认证通过！';
            setTimeout(function() { generateDID(phone); }, 500);
          } else if (q.passed === false) {
            clearInterval(poll);
            status.textContent = '认证未通过';
            btn.disabled = false; btn.textContent = '重试';
          }
        });
      }, 3000);
    }
  }).catch(function(e) {
    status.textContent = '网络错误: ' + e.message;
    btn.disabled = false; btn.textContent = '重试';
  });
};

function generateDID(phone) {
  fetch(FLOW_API + '/api/register/generate-did', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phone })
  }).then(function(r) { return r.json(); }).then(function(data) {
    if (data.success) {
      var did = data.data.did;
      document.getElementById('reg-did-display').textContent = did;
      document.getElementById('reg-alphaid-display').textContent = '算法: ' + data.data.algorithm + ' | 公钥: ' + data.data.publicKey.substring(0, 20) + '...';
      showRegStep(4);
      // 自动登录
      setTimeout(function() { completeLogin(did, phone); }, 2000);
    } else {
      alert('DID 生成失败: ' + (data.error || ''));
    }
  }).catch(function(e) { alert('网络错误: ' + e.message); });
}

function completeLogin(did, phone) {
  closeFaceAuth();
  isLoggedIn = true;
  currentUserDID = did;
  MY_ALPHA_ID = did;

  var loginBtn = document.getElementById('header-login-btn');
  var profileBtn = document.getElementById('profile-btn');
  if (loginBtn) loginBtn.classList.add('hidden');
  if (profileBtn) profileBtn.classList.remove('hidden');

  var didDisplay = document.getElementById('user-did-display');
  if (didDisplay) didDisplay.textContent = did;
  var settingsDid = document.getElementById('settings-did');
  if (settingsDid) settingsDid.textContent = did;

  // 同步到 alphaid
  syncAlphaid();
  showWorkbench();
}'''

    content = content[:old_func_start] + new_func + content[func_end:]
    print("openFaceAuth replaced")

# 4. Remove old simulateScanSuccess function
old_sim = content.find('function simulateScanSuccess(')
if old_sim >= 0:
    # Find end of function
    brace_depth = 0
    i = old_sim
    started = False
    while i < len(content):
        if content[i] == '{':
            brace_depth += 1
            started = True
        elif content[i] == '}':
            brace_depth -= 1
            if started and brace_depth == 0:
                sim_end = i + 1
                break
        i += 1
    else:
        sim_end = len(content)
    content = content[:old_sim] + content[sim_end:]
    print("simulateScanSuccess removed")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done! New file size: {len(content)} chars")
