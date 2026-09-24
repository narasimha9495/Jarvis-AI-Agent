/**
 * Jarvis AI Agent - Frontend Application
 * Handles WebSocket communication, UI updates, and action management.
 */

// ── Configuration ──
const WS_URL = `ws://${window.location.host}/ws`;
const API_BASE = '/api';

// ── State ──
let ws = null;
let isConnected = false;
let pendingConfirmation = null;
let currentProvider = 'gemini';

// ── DOM Elements ──
// (get references to all key elements on DOMContentLoaded)

// ── WebSocket ──
function connectWebSocket() {
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
        isConnected = true;
        updateConnectionStatus(true);
        console.log('Connected to Jarvis');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    ws.onclose = () => {
        isConnected = false;
        updateConnectionStatus(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// ── Message Handling ──
function handleMessage(data) {
    hideTypingIndicator();
    
    switch (data.type) {
        case 'chat':
            addMessage('assistant', data.content);
            break;
        case 'action':
            addMessage('assistant', data.content);
            refreshSidebar();
            break;
        case 'confirm':
            showConfirmation(data);
            break;
        case 'welcome':
            addMessage('assistant', data.content);
            break;
        case 'error':
            addMessage('assistant', `⚠️ ${data.content}`);
            break;
    }
}

// ── Send Message ──
function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if (!text || !isConnected) return;
    
    addMessage('user', text);
    showTypingIndicator();
    
    ws.send(JSON.stringify({
        type: 'chat',
        content: text,
        provider: currentProvider
    }));
    
    input.value = '';
    input.focus();
}

// ── UI Functions ──
function addMessage(role, content) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    // Support markdown-like formatting
    const formatted = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    
    div.innerHTML = `
        <div class="message-bubble">
            <div class="message-content">${formatted}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        </div>
    `;
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.classList.add('visible');
}

function hideTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.classList.remove('visible');
}

function updateConnectionStatus(connected) {
    const dot = document.getElementById('connectionDot');
    const text = document.getElementById('connectionText');
    if (dot) dot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
    if (text) text.textContent = connected ? 'Online' : 'Reconnecting...';
}

// ── Confirmation Modal ──
function showConfirmation(data) {
    pendingConfirmation = data;
    const modal = document.getElementById('confirmModal');
    const msg = document.getElementById('confirmMessage');
    if (msg) msg.textContent = data.content;
    if (modal) modal.classList.add('visible');
}

function confirmAction() {
    if (pendingConfirmation && ws) {
        ws.send(JSON.stringify({
            type: 'confirm',
            content: 'confirmed',
            action: pendingConfirmation.action,
            params: pendingConfirmation.params
        }));
    }
    closeModal();
}

function cancelAction() {
    addMessage('assistant', 'Action cancelled.');
    closeModal();
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    if (modal) modal.classList.remove('visible');
    pendingConfirmation = null;
}

// ── Sidebar Data Loading ──
async function loadTasks() {
    try {
        const res = await fetch(`${API_BASE}/tasks`);
        const tasks = await res.json();
        const container = document.getElementById('tasksList');
        if (!container) return;
        container.innerHTML = tasks.length ? '' : '<p class="empty">No tasks yet</p>';
        
        tasks.forEach(task => {
            const div = document.createElement('div');
            div.className = `sidebar-item ${task.completed ? 'completed' : ''}`;
            div.innerHTML = `
                <div class="item-header">
                    <input type="checkbox" ${task.completed ? 'checked' : ''} 
                           onchange="toggleTask(${task.id})">
                    <span class="item-title">${task.title}</span>
                    <span class="priority priority-${task.priority}">${task.priority}</span>
                </div>
                ${task.description ? `<p class="item-desc">${task.description}</p>` : ''}
                <button class="btn-delete" onclick="deleteTask(${task.id})">✕</button>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to load tasks:', e);
    }
}

async function loadReminders() {
    try {
        const res = await fetch(`${API_BASE}/reminders`);
        const reminders = await res.json();
        const container = document.getElementById('remindersList');
        if (!container) return;
        container.innerHTML = reminders.length ? '' : '<p class="empty">No reminders</p>';
        
        reminders.forEach(rem => {
            const div = document.createElement('div');
            div.className = `sidebar-item ${rem.triggered ? 'completed' : ''}`;
            div.innerHTML = `
                <div class="item-header">
                    <span class="item-title">🔔 ${rem.message}</span>
                </div>
                <p class="item-desc">${new Date(rem.remind_at).toLocaleString()}</p>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to load reminders:', e);
    }
}

async function loadNotes() {
    try {
        const res = await fetch(`${API_BASE}/notes`);
        const notes = await res.json();
        const container = document.getElementById('notesList');
        if (!container) return;
        container.innerHTML = notes.length ? '' : '<p class="empty">No notes yet</p>';
        
        notes.forEach(note => {
            const div = document.createElement('div');
            div.className = 'sidebar-item';
            div.innerHTML = `
                <div class="item-header">
                    <span class="item-title">📝 ${note.title}</span>
                </div>
                <p class="item-desc">${note.content.substring(0, 100)}${note.content.length > 100 ? '...' : ''}</p>
                ${note.tags ? `<div class="tags">${note.tags.split(',').map(t => `<span class="tag">${t.trim()}</span>`).join('')}</div>` : ''}
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to load notes:', e);
    }
}

function refreshSidebar() {
    loadTasks();
    loadReminders();
    loadNotes();
}

// ── Task Actions ──
async function toggleTask(id) {
    await fetch(`${API_BASE}/tasks/${id}/complete`, { method: 'PATCH' });
    loadTasks();
}

async function deleteTask(id) {
    await fetch(`${API_BASE}/tasks/${id}`, { method: 'DELETE' });
    loadTasks();
}

// ── Quick Actions ──
function quickAction(action) {
    const prompts = {
        'new-task': 'Create a new task: ',
        'set-reminder': 'Set a reminder: ',
        'new-note': 'Create a note: ',
        'web-search': 'Search the web for: '
    };
    const input = document.getElementById('messageInput');
    if(input) {
        input.value = prompts[action] || '';
        input.focus();
    }
}

// ── Tab Switching ──
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    
    const targetBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (targetBtn) targetBtn.classList.add('active');
    
    const targetPanel = document.getElementById(`${tabName}Panel`);
    if (targetPanel) targetPanel.classList.add('active');
}

// ── Provider Switch ──
function switchProvider(provider) {
    currentProvider = provider;
    fetch(`${API_BASE}/providers/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider })
    });
}

// ── Initialize ──
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    refreshSidebar();
    
    // Enter key to send
    const input = document.getElementById('messageInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Provider selector
    const providerSelect = document.getElementById('providerSelect');
    if (providerSelect) {
        providerSelect.addEventListener('change', (e) => switchProvider(e.target.value));
    }
    
    // Load available providers
    fetch(`${API_BASE}/health`).then(r => r.json()).then(data => {
        if (data.available_providers) {
            if (providerSelect) {
                providerSelect.innerHTML = data.available_providers
                    .map(p => `<option value="${p}" ${p === currentProvider ? 'selected' : ''}>${p}</option>`)
                    .join('');
            }
        }
    }).catch(() => {});
});
