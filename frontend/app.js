/**
 * FreeCAD AI 建模助手 - 前端脚本
 * 配色：白色 + 橘色
 * 功能：WebSocket 通信，对话管理，状态监控
 */

// ===================================
// 全局变量
// ===================================

let ws = null;
let isConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let isExporting = false; // 跟踪导出状态
let exportTimeout = null; // 导出超时定时器
let currentExportFormat = null; // 当前导出的格式

// DOM 元素
const elements = {
    // 状态栏
    freecadDot: document.getElementById('freecadDot'),
    freecadText: document.getElementById('freecadText'),
    aiDot: document.getElementById('aiDot'),
    aiText: document.getElementById('aiText'),
    
    // 左侧面板
    modelViewer: document.getElementById('modelViewer'),
    refreshModel: document.getElementById('refreshModel'),
    exportModel: document.getElementById('exportModel'),
    objectCount: document.getElementById('objectCount'),
    activeObject: document.getElementById('activeObject'),
    
    // 右侧面板
    chatMessages: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    clearChat: document.getElementById('clearChat'),
    charCount: document.getElementById('charCount'),
    
    // 加载和通知
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    cancelLoadingBtn: document.getElementById('cancelLoadingBtn'),
    toast: document.getElementById('toast')
};

// ===================================
// 初始化
// ===================================

window.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 FreeCAD AI 助手启动...');
    initEventListeners();
    connectWebSocket();
    checkBackendHealth();
});

// ===================================
// WebSocket 连接
// ===================================

function connectWebSocket() {
    // 修复：当直接打开 HTML 文件时，window.location.hostname 为空
    // 始终连接到 localhost:8001
    const hostname = window.location.hostname || 'localhost';
    const wsUrl = `ws://${hostname}:8001/ws`;
    console.log('连接 WebSocket:', wsUrl);
    
    updateLoadingState('正在连接服务器...');
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('✓ WebSocket 已连接');
            isConnected = true;
            reconnectAttempts = 0;
            hideLoading();
            updateConnectionStatus(true);
            showToast('已连接到服务器 ✓', 'success');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleServerMessage(data);
            } catch (error) {
                console.error('消息解析失败:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
            showToast('连接错误', 'error');
        };
        
        ws.onclose = () => {
            console.log('WebSocket 已断开');
            isConnected = false;
            updateConnectionStatus(false);
            
            // 尝试重连
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
                console.log(`${delay}ms 后尝试重连 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
                setTimeout(connectWebSocket, delay);
                showToast(`连接断开，${delay/1000}秒后重连...`, 'warning');
            } else {
                hideLoading();
                showToast('无法连接到服务器，请检查后端是否运行', 'error');
            }
        };
    } catch (error) {
        console.error('WebSocket 创建失败:', error);
        hideLoading();
        showToast('无法创建 WebSocket 连接', 'error');
    }
}

// ===================================
// 消息处理
// ===================================

function handleServerMessage(data) {
    console.log('收到消息:', data);
    
    const { type, content } = data;
    
    switch (type) {
        case 'status':
            addStatusMessage(content);
            break;
        
        case 'thinking':
            // 显示思考过程（带特殊样式）
            addThinkingMessage(content);
            break;
        
        case 'plan':
            // 显示执行计划
            addPlanMessage(content);
            break;
        
        case 'step_start':
            // 显示步骤开始
            addStepStartMessage(data.step, data.total, data.description);
            break;
            
        case 'code':
            addCodeMessage(content, data.step, data.explanation);
            break;
        
        case 'execution_result':
            // 显示执行结果
            addExecutionResult(content, data.step);
            break;
            
        case 'response':
            addAssistantMessage(content, data.code);
            break;
            
        case 'screenshot':
            addScreenshot(content);
            break;
            
        case 'scene_info':
            updateSceneInfo(content);
            break;
        
        case 'stl_exported':
            // 处理 STL 导出
            if (isExporting) {
                isExporting = false;
                clearTimeout(exportTimeout);
            }
            hideLoading();
            console.log('收到 STL 数据，长度:', content ? content.length : 0);
            
            if (content) {
                loadSTLFromBase64(content);
                
                // 自动请求更新场景信息
                requestSceneInfo();
                
                // 如果是自动导出，显示友好提示
                if (data.auto) {
                    showToast('✓ 3D 模型已更新', 'success');
                } else {
                    showToast(data.message || 'STL 导出成功', 'success');
                }
            } else {
                showToast('STL 数据为空', 'error');
            }
            break;
        
        case 'model_exported':
            // 处理多格式模型导出
            isExporting = false; // 重置导出状态
            clearTimeout(exportTimeout); // 清除超时定时器
            hideLoading(); // 关闭加载动画
            
            console.log(`收到 ${data.format.toUpperCase()} 数据，长度:`, content ? content.length : 0);
            
            if (content) {
                // 下载文件
                downloadModelFile(content, data.format);
                showToast(data.message || `${data.format.toUpperCase()} 导出成功`, 'success');
            } else {
                showToast(`${data.format.toUpperCase()} 数据为空`, 'error');
            }
            break;
            
        case 'error':
            // 导出失败时取消导出状态
            console.log('收到错误消息:', content, '当前导出状态:', isExporting);
            
            if (isExporting) {
                isExporting = false;
                clearTimeout(exportTimeout);
                hideLoading();
                addErrorMessage(content);
                showToast('导出失败: ' + content, 'error');
            } else {
                addErrorMessage(content);
                showToast('操作失败: ' + content, 'error');
            }
            break;
            
        default:
            console.warn('未知消息类型:', type);
    }
}

// ===================================
// 消息显示函数
// ===================================

function addUserMessage(text) {
    const messageDiv = createMessageElement('user', text);
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addAssistantMessage(text, code = null) {
    const messageDiv = createMessageElement('assistant', text);
    
    if (code) {
        const codeBlock = document.createElement('div');
        codeBlock.className = 'code-block';
        codeBlock.textContent = code;
        messageDiv.querySelector('.message-text').appendChild(codeBlock);
    }
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addStatusMessage(text) {
    const messageDiv = createMessageElement('assistant', text, true);
    messageDiv.querySelector('.message-text').classList.add('status-message');
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addCodeMessage(code, step = null, explanation = null) {
    const header = step ? `步骤 ${step} - ${explanation || '生成代码'}` : '生成的 FreeCAD Python 代码：';
    const messageDiv = createMessageElement('assistant', header);
    const codeBlock = document.createElement('div');
    codeBlock.className = 'code-block';
    codeBlock.textContent = code;
    messageDiv.querySelector('.message-text').appendChild(codeBlock);
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addThinkingMessage(text) {
    const messageDiv = createMessageElement('assistant', '💭 ' + text);
    messageDiv.querySelector('.message-text').classList.add('thinking-message');
    messageDiv.querySelector('.message-text').style.cssText = `
        background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
        border-left: 4px solid #ff8c42;
        font-style: italic;
        color: #9a3412;
    `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addPlanMessage(text) {
    const messageDiv = createMessageElement('assistant', '📋 ' + text);
    messageDiv.querySelector('.message-text').style.cssText = `
        background: #f0f9ff;
        border-left: 4px solid #0ea5e9;
        white-space: pre-wrap;
        font-family: 'Consolas', monospace;
        color: #0c4a6e;
    `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addStepStartMessage(step, total, description) {
    const messageDiv = createMessageElement('assistant', `🔧 [${step}/${total}] ${description}`);
    messageDiv.querySelector('.message-text').style.cssText = `
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        font-weight: 600;
        color: #92400e;
    `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addExecutionResult(result, step = null) {
    const header = step ? `✓ 步骤 ${step} 执行结果：` : '执行结果：';
    const messageDiv = createMessageElement('assistant', header);
    const resultBlock = document.createElement('div');
    resultBlock.className = 'execution-result';
    resultBlock.style.cssText = `
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 6px;
        padding: 12px;
        margin-top: 8px;
        font-family: 'Consolas', monospace;
        font-size: 13px;
        color: #166534;
        white-space: pre-wrap;
    `;
    resultBlock.textContent = result;
    messageDiv.querySelector('.message-text').appendChild(resultBlock);
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addScreenshot(base64Data) {
    const messageDiv = createMessageElement('assistant', 'FreeCAD 截图：');
    const screenshotDiv = document.createElement('div');
    screenshotDiv.className = 'screenshot-preview';
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${base64Data}`;
    img.alt = 'FreeCAD 截图';
    screenshotDiv.appendChild(img);
    messageDiv.querySelector('.message-text').appendChild(screenshotDiv);
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addErrorMessage(text) {
    const messageDiv = createMessageElement('assistant', '❌ ' + text);
    messageDiv.querySelector('.message-text').style.background = '#FFEBEE';
    messageDiv.querySelector('.message-text').style.borderColor = '#F44336';
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function createMessageElement(sender, text, isStatus = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessageText(text);
    
    content.appendChild(textDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

function formatMessageText(text) {
    // 简单的文本格式化
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// ===================================
// 发送消息
// ===================================

function sendMessage() {
    const text = elements.messageInput.value.trim();
    
    if (!text) {
        showToast('请输入消息', 'warning');
        return;
    }
    
    if (!isConnected) {
        showToast('未连接到服务器', 'error');
        return;
    }
    
    // 显示用户消息
    addUserMessage(text);
    
    // 发送到服务器
    const message = {
        type: 'chat',
        content: text
    };
    
    try {
        ws.send(JSON.stringify(message));
        console.log('发送消息:', message);
        
        // 清空输入框
        elements.messageInput.value = '';
        updateCharCount();
    } catch (error) {
        console.error('发送失败:', error);
        addErrorMessage('消息发送失败');
        showToast('发送失败', 'error');
    }
}

function requestSceneInfo() {
    if (!isConnected) {
        showToast('未连接到服务器', 'error');
        return;
    }
    
    const message = {
        type: 'get_scene'
    };
    
    try {
        ws.send(JSON.stringify(message));
        console.log('请求场景信息');
        addStatusMessage('正在获取场景信息...');
    } catch (error) {
        console.error('请求失败:', error);
        showToast('请求失败', 'error');
    }
}

function loadBaseModel() {
    if (!isConnected) {
        showToast('未连接到服务器', 'error');
        return;
    }
    
    // 显示加载动画
    updateLoadingState('正在加载基础模型...');
    elements.cancelLoadingBtn.style.display = 'block';
    
    // 发送加载请求
    const message = {
        type: 'load_base_model'
    };
    
    try {
        ws.send(JSON.stringify(message));
        console.log('已发送加载基础模型请求');
        addStatusMessage('📁 正在加载基础模型（chairset.blend）...');
    } catch (error) {
        console.error('请求失败:', error);
        showToast('加载失败', 'error');
        hideLoading();
    }
}

// ===================================
// 场景信息更新
// ===================================

function updateSceneInfo(sceneData) {
    if (!sceneData) return;
    
    // 更新对象计数
    elements.objectCount.textContent = sceneData.object_count || 0;
    
    // 更新活动对象
    elements.activeObject.textContent = sceneData.active_object || '无';
    
    // 在聊天中显示详细信息
    let infoText = `📊 <strong>场景信息：</strong><br>`;
    infoText += `对象数量：${sceneData.object_count || 0}<br>`;
    infoText += `活动对象：${sceneData.active_object || '无'}`;
    
    if (sceneData.objects && sceneData.objects.length > 0) {
        infoText += '<br><br><strong>对象列表：</strong><br>';
        sceneData.objects.slice(0, 10).forEach(obj => {
            infoText += `• ${obj.name} (${obj.type})<br>`;
        });
        if (sceneData.objects.length > 10) {
            infoText += `... 还有 ${sceneData.objects.length - 10} 个对象`;
        }
    }
    
    addAssistantMessage(infoText);
}

// ===================================
// 状态管理
// ===================================

function updateConnectionStatus(connected) {
    if (connected) {
        elements.freecadDot.classList.add('connected');
        elements.freecadText.textContent = 'FreeCAD: 已连接';
        elements.sendBtn.disabled = false;
    } else {
        elements.freecadDot.classList.remove('connected');
        elements.freecadText.textContent = 'FreeCAD: 断开连接';
        elements.sendBtn.disabled = true;
    }
}

async function checkBackendHealth() {
    try {
        const response = await fetch('http://localhost:8001/health');
        const data = await response.json();
        
        // 更新 FreeCAD 状态
        if (data.freecad_connected) {
            elements.freecadDot.classList.add('connected');
            elements.freecadText.textContent = 'FreeCAD: 已连接';
        }
        
        // 更新 AI 状态
        if (data.ai_mode === 'ai_enabled') {
            elements.aiDot.classList.add('connected');
            elements.aiText.textContent = `AI: ${data.ai_model || '已启用'}`;
        } else {
            elements.aiDot.classList.add('connected');
            elements.aiDot.style.background = '#FFC107'; // 黄色表示降级
            elements.aiText.textContent = 'AI: 规则引擎';
        }
        
        console.log('后端健康检查:', data);
    } catch (error) {
        console.error('健康检查失败:', error);
        elements.aiDot.classList.add('error');
        elements.aiText.textContent = 'AI: 未知';
    }
}

// ===================================
// 事件监听
// ===================================

function initEventListeners() {
    // 发送按钮
    elements.sendBtn.addEventListener('click', sendMessage);
    
    // 输入框事件
    elements.messageInput.addEventListener('input', updateCharCount);
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 清空聊天
    elements.clearChat.addEventListener('click', () => {
        if (confirm('确定要清空对话记录吗？')) {
            elements.chatMessages.innerHTML = '';
            showToast('对话已清空', 'success');
        }
    });
    
    // 加载基础模型按钮
    const loadBaseModelBtn = document.getElementById('loadBaseModel');
    if (loadBaseModelBtn) {
        loadBaseModelBtn.addEventListener('click', loadBaseModel);
    }
    
    // 刷新模型
    elements.refreshModel.addEventListener('click', () => {
        requestSceneInfo();
        showToast('正在刷新...', 'info');
    });
    
    // 导出模型 - 使用下拉菜单选择格式
    const exportBtn = document.getElementById('exportModelBtn');
    const formatSelect = document.getElementById('formatSelect');
    
    if (exportBtn && formatSelect) {
        exportBtn.addEventListener('click', () => {
            const selectedFormat = formatSelect.value;
            console.log(`导出格式: ${selectedFormat}`);
            exportModelDirect(selectedFormat);
        });
    }
    
    // 取消导出按钮
    if (elements.cancelLoadingBtn) {
        elements.cancelLoadingBtn.addEventListener('click', cancelExport);
    }
    
    // 快捷按钮
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const text = btn.dataset.text;
            elements.messageInput.value = text;
            updateCharCount();
            sendMessage();
        });
    });
}

function updateCharCount() {
    const count = elements.messageInput.value.length;
    elements.charCount.textContent = count;
    elements.sendBtn.disabled = count === 0 || !isConnected;
}

// ===================================
// UI 辅助函数
// ===================================

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function updateLoadingState(text) {
    elements.loadingOverlay.querySelector('.loading-text').textContent = text;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
    elements.cancelLoadingBtn.style.display = 'none';
}

function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = 'toast show';
    
    // 根据类型设置颜色
    const colors = {
        success: '#4CAF50',
        error: '#F44336',
        warning: '#FFC107',
        info: '#FF8C42'
    };
    elements.toast.style.borderLeftColor = colors[type] || colors.info;
    
    // 3秒后隐藏
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

// ===================================
// 工具函数
// ===================================

function formatTimestamp() {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
}

// ===================================
// 调试函数
// ===================================

window.debugInfo = () => {
    console.log('=== 调试信息 ===');
    console.log('WebSocket 状态:', isConnected ? '已连接' : '未连接');
    console.log('重连尝试次数:', reconnectAttempts);
    console.log('消息数量:', elements.chatMessages.children.length);
    console.log('');
    console.log('=== 3D 查看器状态 ===');
    console.log('Scene:', typeof scene !== 'undefined' ? '已创建' : '未创建');
    console.log('Camera:', typeof camera !== 'undefined' ? '已创建' : '未创建');
    console.log('Renderer:', typeof renderer !== 'undefined' ? '已创建' : '未创建');
    console.log('Controls:', typeof controls !== 'undefined' ? '已创建' : '未创建');
    console.log('Controls.update:', typeof controls !== 'undefined' ? (typeof controls.update === 'function' ? '✓ 函数' : '✗ 不是函数') : '无');
    console.log('Current Mesh:', currentMesh ? '已加载 (' + currentMesh.geometry.attributes.position.count + ' 顶点)' : '未加载');
    console.log('Current STL Data:', currentSTLData ? '已保存 (' + currentSTLData.length + ' 字符)' : '未保存');
};

console.log('✓ 前端脚本加载完成');
console.log('💡 输入 debugInfo() 查看调试信息');


// ===================================
// Three.js 3D 查看器
// ===================================

let scene, camera, renderer, controls, currentMesh;
let isWireframe = false;
let currentSTLData = null;

function init3DViewer() {
    const canvas = document.getElementById('threeCanvas');
    const container = document.getElementById('modelViewer');
    
    if (!canvas || !container) {
        console.error('找不到 3D 查看器容器');
        return;
    }
    
    // 创建场景
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    
    // 创建相机
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    
    // 创建渲染器
    renderer = new THREE.WebGLRenderer({ 
        canvas: canvas, 
        antialias: true,
        alpha: true
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    
    // 添加轨道控制器
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2;
    controls.maxDistance = 50;
    
    // 添加灯光
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(5, 5, 5);
    scene.add(directionalLight1);
    
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight2.position.set(-5, 3, -5);
    scene.add(directionalLight2);
    
    // 添加网格地面
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    scene.add(gridHelper);
    
    // 添加坐标轴
    const axesHelper = new THREE.AxesHelper(3);
    scene.add(axesHelper);
    
    // 窗口大小改变时调整
    window.addEventListener('resize', onWindowResize, false);
    
    // 启动渲染循环
    animate();
    
    console.log('✓ 3D 查看器初始化完成');
}

function animate() {
    requestAnimationFrame(animate);
    
    if (controls) {
        controls.update();
    }
    
    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}

function onWindowResize() {
    const container = document.getElementById('modelViewer');
    if (!container) return;
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    
    renderer.setSize(width, height);
}

function loadSTLFromBase64(base64Data) {
    console.log('加载 STL 数据...');
    
    // 显示加载动画
    showViewerLoading();
    
    try {
        // 隐藏占位符
        const placeholder = document.getElementById('viewerPlaceholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // 显示控制栏（注意：这里使用不同的变量名避免冲突）
        const viewerControls = document.getElementById('viewerControls');
        if (viewerControls) {
            viewerControls.style.display = 'flex';
        }
        
        // 解码 Base64
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // 使用 STLLoader 加载
        const loader = new THREE.STLLoader();
        let geometry = loader.parse(bytes.buffer);
        
        // 重要：修复坐标轴对齐问题
        // FreeCAD 使用 Z 轴向上，Three.js 使用 Y 轴向上
        // 需要交换 Y 和 Z 坐标来对齐：绕 X 轴旋转 -90 度
        geometry.rotateX(-Math.PI / 2);
        
        // 重新计算几何体
        geometry.computeBoundingBox();
        
        // 移除旧模型
        if (currentMesh) {
            scene.remove(currentMesh);
            currentMesh.geometry.dispose();
            currentMesh.material.dispose();
        }
        
        // 创建材质（橙色金属效果）
        const material = new THREE.MeshPhongMaterial({
            color: 0xff8c42,
            specular: 0x444444,
            shininess: 100,
            flatShading: false,
            side: THREE.DoubleSide
        });
        
        // 创建网格
        currentMesh = new THREE.Mesh(geometry, material);
        
        // 居中模型
        geometry.computeBoundingBox();
        const center = new THREE.Vector3();
        geometry.boundingBox.getCenter(center);
        currentMesh.position.sub(center);
        
        // 添加到场景
        scene.add(currentMesh);
        
        // 调试：打印模型尺寸信息
        const modelSize = new THREE.Vector3();
        geometry.boundingBox.getSize(modelSize);
        console.log('📐 旋转后模型尺寸:', {
            x: modelSize.x.toFixed(2),
            y: modelSize.y.toFixed(2), 
            z: modelSize.z.toFixed(2)
        });
        
        // 显示预期尺寸（来自用户指令）
        console.log('📋 预期尺寸 (FreeCAD XYZ): x=2, y=4, z=6');
        console.log('  转换到 Three.js (旋转 -90° 绕 X 轴后):');
        console.log('    X (宽度) 不变: 2');
        console.log('    Y (高度) 变成: 6 (原来的 Z)');
        console.log('    Z (深度) 变成: 4 (原来的 Y)');
        console.log('  所以应该看到: x=2, y=6, z=4');
        
        // 自动调整相机位置
        const maxDim = Math.max(modelSize.x, modelSize.y, modelSize.z);
        const fov = camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
        cameraZ *= 2.5; // 留点空间
        
        camera.position.set(cameraZ, cameraZ * 0.8, cameraZ);
        camera.lookAt(0, 0, 0);
        
        // 调试：检查 controls 对象
        console.log('controls 类型:', typeof controls);
        console.log('controls:', controls);
        
        if (controls && typeof controls.update === 'function') {
            controls.update();
        } else {
            console.warn('controls 未正确初始化或没有 update 方法');
        }
        
        // 保存 STL 数据（用于下载）
        currentSTLData = base64Data;
        console.log('✓ STL 数据已保存，长度:', currentSTLData.length, '字符');
        
        // 隐藏加载动画
        hideViewerLoading();
        
        console.log('✓ STL 模型加载成功');
        console.log(`  顶点数: ${geometry.attributes.position.count}`);
        console.log(`  尺寸: ${size.x.toFixed(2)} × ${size.y.toFixed(2)} × ${size.z.toFixed(2)}`);
        
    } catch (error) {
        console.error('STL 加载失败:', error);
        hideViewerLoading();
        showToast('3D 模型加载失败', 'error');
    }
}

function showViewerLoading() {
    // 创建加载动画
    let loadingDiv = document.getElementById('viewerLoading');
    if (!loadingDiv) {
        loadingDiv = document.createElement('div');
        loadingDiv.id = 'viewerLoading';
        loadingDiv.className = 'viewer-loading';
        loadingDiv.innerHTML = `
            <div class="spinner"></div>
            <p>加载 3D 模型中...</p>
        `;
        document.getElementById('modelViewer').appendChild(loadingDiv);
    }
    loadingDiv.style.display = 'block';
}

function hideViewerLoading() {
    const loadingDiv = document.getElementById('viewerLoading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

function resetView() {
    if (!camera || !currentMesh) return;
    
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    controls.reset();
    
    showToast('视角已重置', 'success');
}

function toggleWireframe() {
    if (!currentMesh) return;
    
    isWireframe = !isWireframe;
    currentMesh.material.wireframe = isWireframe;
    
    const btn = document.getElementById('toggleWireframe');
    if (btn) {
        btn.textContent = isWireframe ? '🔳 实体' : '🔲 线框';
    }
    
    showToast(isWireframe ? '线框模式' : '实体模式', 'success');
}

function downloadSTL() {
    console.log('下载按钮被点击');
    console.log('currentSTLData 状态:', currentSTLData ? '已设置 (' + currentSTLData.length + ' 字符)' : '未设置');
    
    if (!currentSTLData) {
        showToast('没有可下载的模型', 'error');
        console.error('currentSTLData 为空，无法下载');
        return;
    }
    
    try {
        // 解码 Base64
        const binaryString = atob(currentSTLData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        console.log('✓ Base64 解码成功，字节数:', bytes.length);
        
        // 创建 Blob
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `freecad_model_${Date.now()}.stl`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('✓ STL 文件下载已触发');
        showToast('STL 文件已下载 ✓', 'success');
        
    } catch (error) {
        console.error('下载失败:', error);
        showToast('下载失败: ' + error.message, 'error');
    }
}

function requestSTLExport() {
    if (!isConnected) {
        showToast('未连接到服务器', 'error');
        return;
    }
    
    if (isExporting) {
        showToast('正在导出中，请稍候...', 'warning');
        return;
    }
    
    // 设置导出状态
    isExporting = true;
    currentExportFormat = 'STL';
    
    // 显示加载动画，并显示取消按钮
    updateLoadingState('正在导出 STL...');
    elements.cancelLoadingBtn.style.display = 'block';
    
    // 设置30秒超时
    exportTimeout = setTimeout(() => {
        if (isExporting) {
            cancelExport();
            showToast('导出超时，请检查 FreeCAD 连接', 'error');
        }
    }, 30000);
    
    // 发送导出请求
    ws.send(JSON.stringify({
        type: 'export_stl'
    }));
}

// 绑定事件
document.addEventListener('DOMContentLoaded', () => {
    // 初始化 3D 查看器
    init3DViewer();
    
    // 刷新模型按钮
    const refreshBtn = document.getElementById('refreshModel');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (!isConnected) {
                showToast('未连接到服务器', 'error');
                return;
            }
            requestSTLExport();
        });
    }
    
    // 导出按钮（目前禁用，未来功能）
    const exportBtn = document.getElementById('exportModel');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            showToast('该功能即将推出', 'info');
        });
    }
    
    // 3D 查看器控制按钮
    const resetBtn = document.getElementById('resetView');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetView);
    }
    
    const wireframeBtn = document.getElementById('toggleWireframe');
    if (wireframeBtn) {
        wireframeBtn.addEventListener('click', toggleWireframe);
    }
    
    const downloadBtn = document.getElementById('downloadSTL');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadSTL);
    }
});


// ===================================
// 导出功能（直接导出，无对话框）
// ===================================

function exportModelDirect(format) {
    if (!isConnected) {
        showToast('未连接到服务器', 'error');
        return;
    }
    
    if (isExporting) {
        showToast('正在导出中，请稍候...', 'warning');
        return;
    }
    
    console.log(`导出 ${format.toUpperCase()} 格式...`);
    
    // 显示友好的格式名称
    const formatNames = {
        'stl': 'STL',
        'obj': 'OBJ',
        'fbx': 'FBX',
        'gltf': 'glTF',
        'glb': 'GLB',
        'ply': 'PLY',
        'x3d': 'X3D',
        'dae': 'Collada',
        'abc': 'Alembic'
    };
    
    const formatName = formatNames[format] || format.toUpperCase();
    
    // 设置导出状态
    isExporting = true;
    currentExportFormat = formatName;
    
    // 显示加载动画，并显示取消按钮
    updateLoadingState(`正在导出 ${formatName}...`);
    elements.cancelLoadingBtn.style.display = 'block';
    
    // 设置30秒超时
    exportTimeout = setTimeout(() => {
        if (isExporting) {
            cancelExport();
            showToast('导出超时，请检查 FreeCAD 连接', 'error');
        }
    }, 30000);
    
    // 发送导出请求
    ws.send(JSON.stringify({
        type: 'export_model',
        format: format,
        selection_only: false
    }));
}

// 取消导出操作
function cancelExport() {
    if (!isExporting) return;
    
    console.log('用户取消导出');
    isExporting = false;
    currentExportFormat = null;
    clearTimeout(exportTimeout);
    hideLoading();
    showToast('已取消导出', 'info');
}

function downloadModelFile(base64Data, format) {
    try {
        // 格式扩展名映射
        const extensions = {
            'stl': '.stl',
            'obj': '.obj',
            'fbx': '.fbx',
            'gltf': '.gltf',
            'glb': '.glb',
            'ply': '.ply',
            'x3d': '.x3d',
            'dae': '.dae',
            'abc': '.abc'
        };
        
        const ext = extensions[format] || '.dat';
        
        // 解码 Base64
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        console.log(`✓ Base64 解码成功，字节数: ${bytes.length}`);
        
        // 创建 Blob
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `freecad_model_${Date.now()}${ext}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log(`✓ ${format.toUpperCase()} 文件下载已触发`);
        
    } catch (error) {
        console.error('下载失败:', error);
        showToast('下载失败: ' + error.message, 'error');
    }
}

// ===================================
// 旧版对话框功能（已弃用，改用下拉菜单）
// ===================================

// 这些函数保留但不再使用
// 如果将来需要恢复对话框模式，可以取消注释

/*
function openExportModal() {
    const modal = document.getElementById('exportModal');
    if (modal) {
        modal.style.display = 'flex';
        
        // 绑定格式按钮点击事件
        const formatBtns = modal.querySelectorAll('.format-btn');
        formatBtns.forEach(btn => {
            btn.onclick = () => {
                const format = btn.dataset.format;
                exportModel(format);
                closeExportModal();
            };
        });
    }
}

function closeExportModal() {
    const modal = document.getElementById('exportModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function exportModel(format) {
    if (!isConnected) {
        showToast('未连接到服务器', 'error');
        return;
    }
    
    console.log(`导出 ${format.toUpperCase()} 格式...`);
    
    updateLoadingState(`正在导出 ${format.toUpperCase()}...`);
    
    // 发送导出请求
    ws.send(JSON.stringify({
        type: 'export_model',
        format: format,
        selection_only: false
    }));
}

function downloadModelFile(base64Data, format) {
    try {
        // 格式扩展名映射
        const extensions = {
            'stl': '.stl',
            'obj': '.obj',
            'fbx': '.fbx',
            'gltf': '.gltf',
            'glb': '.glb',
            'ply': '.ply',
            'x3d': '.x3d',
            'dae': '.dae',
            'abc': '.abc'
        };
        
        const ext = extensions[format] || '.dat';
        
        // 解码 Base64
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        console.log(`✓ Base64 解码成功，字节数: ${bytes.length}`);
        
        // 创建 Blob
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `freecad_model_${Date.now()}${ext}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log(`✓ ${format.toUpperCase()} 文件下载已触发`);
        
    } catch (error) {
        console.error('下载失败:', error);
        showToast('下载失败: ' + error.message, 'error');
    }
}
*/

// 对话框相关的事件监听也已禁用
// 如需恢复，取消下面代码的注释

/*
// 关闭对话框（点击背景）
document.addEventListener('click', (e) => {
    const modal = document.getElementById('exportModal');
    if (modal && e.target === modal) {
        closeExportModal();
    }
});

// ESC 键关闭对话框
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeExportModal();
    }
});
*/
