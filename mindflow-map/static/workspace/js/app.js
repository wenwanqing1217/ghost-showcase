// MindFlow Workspace 前端逻辑 - 已接入真实后端 API

// 当前标签页
let currentTab = 'dashboard';

// API 基础地址
const API_BASE = window.location.origin;

// 切换标签页
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
    });

    const target = document.getElementById('tab-' + tabId);
    if (target) {
        target.classList.remove('hidden');
    }

    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('bg-indigo-50', 'text-indigo-700');
        el.classList.add('text-gray-600', 'hover:bg-gray-50', 'hover:text-gray-900');
    });

    const activeNav = document.getElementById('nav-' + tabId);
    if (activeNav) {
        activeNav.classList.remove('text-gray-600', 'hover:bg-gray-50', 'hover:text-gray-900');
        activeNav.classList.add('bg-indigo-50', 'text-indigo-700');
    }

    const titles = {
        'dashboard': '工作台',
        'chat': 'AI 对话',
        'map': '地图助理',
        'drama': '短剧管理',
        'shopify': '电商运营',
        'bookmarks': '书签收藏'
    };
    document.getElementById('page-title').textContent = titles[tabId] || 'MindFlow';

    currentTab = tabId;
}

// 打开外部链接
function openExternal(url) {
    window.open(url, '_blank');
}

// 通用 API 请求
async function apiRequest(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`API 请求失败 (${response.status}): ${text}`);
    }

    return response.json();
}

// 发送聊天消息
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const messagesContainer = document.getElementById('chat-messages');

    // 添加用户消息
    const userMsg = document.createElement('div');
    userMsg.className = 'flex gap-4 justify-end chat-message';
    userMsg.innerHTML = `
        <div class="bg-indigo-600 text-white rounded-lg rounded-tr-none px-4 py-3 text-sm max-w-2xl">
            ${escapeHtml(message)}
        </div>
        <div class="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center text-gray-600 font-bold text-sm flex-shrink-0">你</div>
    `;
    messagesContainer.appendChild(userMsg);
    input.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // 添加加载状态
    const loadingId = 'loading-' + Date.now();
    const loadingMsg = document.createElement('div');
    loadingMsg.id = loadingId;
    loadingMsg.className = 'flex gap-4 chat-message';
    loadingMsg.innerHTML = `
        <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 font-bold text-sm flex-shrink-0">M</div>
        <div class="bg-gray-50 rounded-lg rounded-tl-none px-4 py-3 text-sm text-gray-500">
            <span class="loading-dots">MindFlow 正在思考</span>
        </div>
    `;
    messagesContainer.appendChild(loadingMsg);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const result = await apiRequest('/api/v1/workflow/execute', {
            method: 'POST',
            body: JSON.stringify({ text: message, user_id: 'workspace' }),
        });

        const replyText = result.result?.text || result.result?.reply || '已收到，但暂无回复内容。';

        // 移除加载状态
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        // 添加 AI 回复
        const aiMsg = document.createElement('div');
        aiMsg.className = 'flex gap-4 chat-message';
        aiMsg.innerHTML = `
            <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 font-bold text-sm flex-shrink-0">M</div>
            <div class="bg-gray-50 rounded-lg rounded-tl-none px-4 py-3 text-sm text-gray-700 max-w-2xl whitespace-pre-wrap">${escapeHtml(replyText)}</div>
        `;
        messagesContainer.appendChild(aiMsg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        const errorMsg = document.createElement('div');
        errorMsg.className = 'flex gap-4 chat-message';
        errorMsg.innerHTML = `
            <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center text-red-600 font-bold text-sm flex-shrink-0">!</div>
            <div class="bg-red-50 rounded-lg rounded-tl-none px-4 py-3 text-sm text-red-700">
                出错了：${escapeHtml(error.message)}
            </div>
        `;
        messagesContainer.appendChild(errorMsg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// 地图查询
async function searchMap() {
    const query = document.getElementById('map-query').value.trim();
    const resultDiv = document.getElementById('map-result');
    if (!query) return;

    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = '<p class="loading-dots text-gray-500">正在查询</p>';

    try {
        const result = await apiRequest('/api/v1/map/search', {
            method: 'POST',
            body: JSON.stringify({ query }),
        });

        const data = result.data || {};
        const pois = data.results || [];

        if (data.message && data.message !== "ok") {
            resultDiv.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
                    地图查询暂时不可用：${escapeHtml(data.message)}
                </div>
            `;
            return;
        }

        if (!pois.length) {
            resultDiv.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
                    未找到相关地点，请换个关键词试试。
                </div>
            `;
            return;
        }

        const lines = pois.slice(0, 5).map((poi, idx) => {
            const name = escapeHtml(poi.name || '未知');
            const address = escapeHtml(poi.address || '');
            const rating = poi.overall_rating ? `，评分 ${escapeHtml(String(poi.overall_rating))}` : '';
            const tag = poi.tag || '';
            return `<li class="flex items-start gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center">${idx + 1}</span>
                <div>
                    <p class="font-medium text-gray-900">${name}${tag ? ` <span class="text-xs text-gray-500">${escapeHtml(tag)}</span>` : ''}</p>
                    ${address ? `<p class="text-xs text-gray-500">${address}</p>` : ''}
                    ${rating ? `<p class="text-xs text-gray-500">${rating}</p>` : ''}
                </div>
            </li>`;
        }).join('');

        resultDiv.innerHTML = `
            <div class="space-y-3">
                <p class="text-sm font-medium text-gray-900">找到 ${pois.length} 个结果，显示前 ${Math.min(pois.length, 5)} 个：</p>
                <ul class="space-y-2">${lines}</ul>
                ${data.resource_key ? `<p class="text-xs text-gray-500 mt-2">地图资源 key：${escapeHtml(data.resource_key)}</p>` : ''}
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
                查询失败：${escapeHtml(error.message)}
            </div>
        `;
    }
}

// 路线规划
async function planRoute() {
    const origin = document.getElementById('route-origin').value.trim();
    const destination = document.getElementById('route-destination').value.trim();
    const resultDiv = document.getElementById('route-result');

    if (!origin || !destination) {
        alert('请填写起点和终点');
        return;
    }

    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = '<p class="loading-dots text-gray-500">正在规划路线</p>';

    try {
        const result = await apiRequest('/api/v1/map/route', {
            method: 'POST',
            body: JSON.stringify({ origin, destination, mode: 'driving' }),
        });

        const data = result.data || {};
        const apiResult = data.result || {};
        const nav = apiResult.navigation_data || {};
        const routes = nav.driving_routes || nav.routes || [];

        if (data.message && data.message !== "ok") {
            resultDiv.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
                    路线规划暂时不可用：${escapeHtml(data.message)}
                </div>
            `;
            return;
        }

        if (!routes.length) {
            resultDiv.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
                    未找到可用路线，请检查地址是否正确。
                </div>
            `;
            return;
        }

        const route = routes[0];
        const distance = route.distance || '未知';
        const duration = route.duration || '未知';
        let durationStr = String(duration);
        if (typeof duration === 'number') {
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            durationStr = seconds ? `${minutes}分钟${seconds}秒` : `${minutes}分钟`;
        }

        resultDiv.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
                <p class="font-medium mb-1">路线规划成功</p>
                <p>距离：${distance} 米</p>
                <p>预计耗时：${durationStr}</p>
                        ${data.resource_key ? `<p class="text-xs text-gray-500 mt-2">地图资源 key：${escapeHtml(data.resource_key)}</p>` : ''}
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
                路线规划失败：${escapeHtml(error.message)}
            </div>
        `;
    }
}

// 添加书签
function addBookmark() {
    const url = prompt('请输入网站地址：');
    if (!url) return;

    const name = prompt('请输入网站名称：') || url;
    const grid = document.getElementById('bookmarks-grid');

    if (grid.querySelector('.text-center')) {
        grid.innerHTML = '<div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4" id="bookmarks-list"></div>';
    }

    const list = document.getElementById('bookmarks-list');
    if (!list) {
        const newList = document.createElement('div');
        newList.id = 'bookmarks-list';
        newList.className = 'grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4';
        grid.innerHTML = '';
        grid.appendChild(newList);
    }

    const currentList = document.getElementById('bookmarks-list');
    const card = document.createElement('button');
    card.onclick = () => openExternal(url);
    card.className = 'group flex flex-col items-center justify-center p-4 bg-white rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-md transition-all hover-lift';
    card.innerHTML = `
        <div class="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center text-2xl mb-2 group-hover:scale-110 transition-transform">🔗</div>
        <span class="text-sm font-medium text-gray-700 text-center truncate w-full">${escapeHtml(name)}</span>
        <span class="text-xs text-gray-400 truncate w-full text-center">${escapeHtml(url)}</span>
    `;
    currentList.appendChild(card);
}

// 显示配置引导
function showSetupGuide(platform) {
    const modal = document.getElementById('setup-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');

    const guides = {
        'feishu': {
            title: '配置飞书机器人',
            content: `
                <div class="space-y-4">
                    <p>要让 MindFlow 在飞书里跟你对话，你需要创建一个飞书机器人应用：</p>
                    <ol class="list-decimal list-inside space-y-2 text-gray-700">
                        <li>打开 <a href="https://open.feishu.cn" target="_blank" class="text-indigo-600 hover:underline">飞书开放平台</a>，登录你的飞书账号</li>
                        <li>点击「创建企业自建应用」</li>
                        <li>填写应用名称（如：MindFlow 助手）和描述</li>
                        <li>进入应用后，在左侧菜单找到「事件与回调」</li>
                        <li>添加事件：<code>im.message.receive_v1</code>（接收消息）</li>
                        <li>在「版本管理与发布」中创建版本并发布</li>
                        <li>在应用的「凭证与基础信息」页面，复制 App ID 和 App Secret</li>
                    </ol>
                    <p class="text-sm text-gray-500">拿到 App ID 和 App Secret 后，发给我，我帮你配置到 MindFlow。</p>
                </div>
            `
        },
        'shopify': {
            title: '配置 Shopify',
            content: `
                <div class="space-y-4">
                    <p>要让 MindFlow 自动管理你的 Shopify 店铺：</p>
                    <ol class="list-decimal list-inside space-y-2 text-gray-700">
                        <li>登录你的 <a href="https://shopify.com" target="_blank" class="text-indigo-600 hover:underline">Shopify 后台</a></li>
                        <li>进入「设置」→「应用和销售渠道」</li>
                        <li>点击「开发应用」→「创建应用」</li>
                        <li>配置 Admin API 权限，至少需要：<code>read_orders</code>, <code>read_products</code></li>
                        <li>安装应用后，复制 Access Token</li>
                    </ol>
                    <p class="text-sm text-gray-500">拿到 Access Token 后，发给我，我帮你配置。</p>
                </div>
            `
        },
        'douyin': {
            title: '配置抖音短剧',
            content: `
                <div class="space-y-4">
                    <p>要让 MindFlow 自动发布短剧到抖音：</p>
                    <ol class="list-decimal list-inside space-y-2 text-gray-700">
                        <li>登录 <a href="https://www.douyin.com" target="_blank" class="text-indigo-600 hover:underline">抖音创作者服务平台</a></li>
                        <li>完成账号实名认证</li>
                        <li>进入「内容管理」→「视频上传」</li>
                        <li>目前 MindFlow 使用浏览器自动化方式操作，需要你提供账号信息</li>
                    </ol>
                    <p class="text-sm text-gray-500">后续我们会逐步接入抖音官方 API，实现更稳定的自动发布。</p>
                </div>
            `
        }
    };

    const guide = guides[platform];
    if (guide) {
        title.textContent = guide.title;
        body.innerHTML = guide.content;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

// 关闭弹窗
function closeSetupModal() {
    const modal = document.getElementById('setup-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// HTML 转义防止 XSS
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    switchTab('dashboard');
});
