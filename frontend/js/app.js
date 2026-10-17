/**
 * Jarvis AI Agent — Personalised Frontend
 * Features: themes, AI personality, chat history, mood system, smart suggestions
 */

// ── Configuration ──
const WS_URL = `ws://${window.location.host}/ws`;
const API_BASE = '/api';
const STORAGE_KEY = 'jarvis_settings';
const HISTORY_KEY = 'jarvis_chat_history';

// ── State ──
let ws = null;
let isConnected = false;
let pendingConfirmation = null;
let currentProvider = 'gemini';
let messageCount = 0;

// ── Default Settings ──
const defaultSettings = {
    userName: 'Narasimha',
    theme: 'dark',
    personality: 'friendly',
    responseStyle: 'balanced',
};

let settings = loadSettings();

// ── Settings Persistence ──
function loadSettings() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? { ...defaultSettings, ...JSON.parse(saved) } : { ...defaultSettings };
    } catch {
        return { ...defaultSettings };
    }
}

function saveSettings() {
    const nameEl = document.getElementById('userName');
    const personalityEl = document.getElementById('aiPersonality');
    const styleEl = document.getElementById('responseStyle');

    if (nameEl) settings.userName = nameEl.value || 'User';
    if (personalityEl) settings.personality = personalityEl.value;
    if (styleEl) settings.responseStyle = styleEl.value;

    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    applySettings();
}

function applySettings() {
    // Update greeting
    const nameEl = document.getElementById('greetingName');
    if (nameEl) nameEl.textContent = settings.userName;

    // Update settings inputs
    const userNameInput = document.getElementById('userName');
    if (userNameInput && userNameInput.value !== settings.userName) {
        userNameInput.value = settings.userName;
    }

    const personalityEl = document.getElementById('aiPersonality');
    if (personalityEl) personalityEl.value = settings.personality;

    const styleEl = document.getElementById('responseStyle');
    if (styleEl) styleEl.value = settings.responseStyle;

    // Update theme buttons
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === settings.theme);
    });
}

// ── Theme System ──
function setTheme(theme) {
    document.body.dataset.theme = theme;
    settings.theme = theme;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));

    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.textContent = theme === 'light' ? '☀️' : theme === 'midnight' ? '🌌' : '🌙';
    }

    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });
}

function toggleTheme() {
    const themes = ['dark', 'midnight', 'light'];
    const idx = themes.indexOf(settings.theme);
    setTheme(themes[(idx + 1) % themes.length]);
}

// ── Greeting System ──
function updateGreeting() {
    const hour = new Date().getHours();
    let greeting;
    if (hour < 6) greeting = 'Good Night';
    else if (hour < 12) greeting = 'Good Morning';
    else if (hour < 17) greeting = 'Good Afternoon';
    else if (hour < 21) greeting = 'Good Evening';
    else greeting = 'Good Night';

    const el = document.getElementById('greetingTime');
    if (el) el.textContent = greeting;

    const dateEl = document.getElementById('greetingDate');
    if (dateEl) {
        dateEl.textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'long', month: 'short', day: 'numeric'
        });
    }
}

function getWelcomeMessage() {
    const hour = new Date().getHours();
    const name = settings.userName;
    const messages = {
        professional: `Welcome back, ${name}. All systems are operational. How may I assist you today?`,
        friendly: `Hey ${name}! 😊 Great to see you! I'm ready to help with whatever you need today.`,
        casual: `Yo ${name}! What's up? Ready to get stuff done? 🚀`,
        motivational: `${name}! 💪 Every moment is a fresh start. Let's make today count! What's on the agenda?`,
    };
    return messages[settings.personality] || messages.friendly;
}

// ── Mood System ──
const moods = [
    { emoji: '😊', text: 'Ready to help', threshold: 0 },
    { emoji: '🤔', text: 'Thinking deeply', threshold: 3 },
    { emoji: '💡', text: 'Full of ideas', threshold: 6 },
    { emoji: '🔥', text: 'On fire!', threshold: 10 },
    { emoji: '🧠', text: 'Deep focus mode', threshold: 15 },
    { emoji: '⚡', text: 'Supercharged!', threshold: 20 },
];

function updateMood() {
    const mood = [...moods].reverse().find(m => messageCount >= m.threshold) || moods[0];
    const emojiEl = document.getElementById('moodEmoji');
    const textEl = document.getElementById('moodText');
    if (emojiEl) emojiEl.textContent = mood.emoji;
    if (textEl) textEl.textContent = mood.text;
}

// ── Chat History ──
function saveChatHistory() {
    try {
        const messages = document.getElementById('chatMessages');
        if (!messages) return;
        const items = [];
        messages.querySelectorAll('.message').forEach(msg => {
            const role = msg.classList.contains('user') ? 'user' : 'assistant';
            const content = msg.querySelector('.message-content')?.textContent || '';
            const time = msg.querySelector('.message-time')?.textContent || '';
            if (content) items.push({ role, content, time });
        });
        // Keep last 50 messages
        const trimmed = items.slice(-50);
        localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
    } catch { /* storage full, ignore */ }
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem(HISTORY_KEY);
        if (!saved) return;
        const items = JSON.parse(saved);
        // Only restore last 20 messages to keep it clean
        items.slice(-20).forEach(item => {
            addMessage(item.role, item.content, item.time, true);
        });
    } catch { /* corrupt data, ignore */ }
}

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
            messageCount++;
            updateMood();
            break;
        case 'action':
            addMessage('assistant', data.content);
            refreshSidebar();
            messageCount++;
            updateMood();
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
    messageCount++;
    updateMood();
    
    ws.send(JSON.stringify({
        type: 'chat',
        content: text,
        provider: currentProvider,
        personality: settings.personality,
        response_style: settings.responseStyle,
    }));
    
    input.value = '';
    input.focus();
}

// ── UI Functions ──
function addMessage(role, content, customTime = null, skipSave = false) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    const formatted = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    
    const timeStr = customTime || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    div.innerHTML = `
        <div class="message-bubble">
            <div class="message-content">${formatted}</div>
            <div class="message-time">${timeStr}</div>
        </div>
    `;
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    if (!skipSave) saveChatHistory();
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

// ── Settings Modal ──
function openSettings() {
    applySettings();
    const modal = document.getElementById('settingsModal');
    if (modal) modal.classList.add('visible');
}

function closeSettings() {
    const modal = document.getElementById('settingsModal');
    if (modal) modal.classList.remove('visible');
}

// ── Smart Suggestions ──
function useSuggestion(text) {
    const input = document.getElementById('messageInput');
    if (input) {
        input.value = text;
        sendMessage();
    }
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
    loadExpenses();
    loadHabits();
    loadSystemStatus();
}

// ── Expense Loading ──
async function loadExpenses() {
    try {
        const res = await fetch(`${API_BASE}/expenses`);
        const data = await res.json();
        const expenses = data.expenses || [];
        const container = document.getElementById('expensesList');
        if (!container) return;
        container.innerHTML = expenses.length ? '' : '<p class="empty">No expenses yet</p>';

        expenses.forEach(exp => {
            const div = document.createElement('div');
            div.className = 'sidebar-item';
            div.innerHTML = `
                <div class="item-header">
                    <span class="item-title">💰 $${exp.amount.toFixed(2)}</span>
                    <span class="priority priority-${exp.category}">${exp.category}</span>
                </div>
                ${exp.description ? `<p class="item-desc">${exp.description}</p>` : ''}
                <p class="item-desc" style="font-size:11px;">${exp.date}</p>
            `;
            container.appendChild(div);
        });

        const summaryEl = document.getElementById('expensesSummary');
        if (summaryEl && data.total !== undefined) {
            summaryEl.textContent = `Total: $${data.total.toFixed(2)} (${expenses.length} items)`;
        }
    } catch (e) {
        console.error('Failed to load expenses:', e);
    }
}

// ── Habit Loading ──
async function loadHabits() {
    try {
        const res = await fetch(`${API_BASE}/habits`);
        const data = await res.json();
        const habits = data.habits || [];
        const container = document.getElementById('habitsList');
        if (!container) return;
        container.innerHTML = habits.length ? '' : '<p class="empty">No habits yet</p>';

        habits.forEach(habit => {
            const div = document.createElement('div');
            div.className = 'sidebar-item';
            div.innerHTML = `
                <div class="item-header">
                    <span class="item-title">✅ ${habit.name}</span>
                    <span class="priority priority-high">🔥 ${habit.current_streak}d</span>
                </div>
                <p class="item-desc">${habit.total_completions} total | ${habit.frequency}</p>
                <button class="btn-delete" onclick="logHabit(${habit.id})" title="Log today" style="right:30px;display:block;">✓</button>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to load habits:', e);
    }
}

async function logHabit(id) {
    await fetch(`${API_BASE}/habits/${id}/log`, { method: 'POST' });
    loadHabits();
}

// ── System Status ──
async function loadSystemStatus() {
    try {
        const res = await fetch(`${API_BASE}/system/status`);
        const data = await res.json();
        if (data.success) {
            const cpuVal = data.cpu_percent;
            const ramVal = data.memory.percent;
            const diskVal = data.disk.percent;

            const cpu = document.getElementById('sysCpu');
            const ram = document.getElementById('sysRam');
            const disk = document.getElementById('sysDisk');
            const cpuBar = document.getElementById('cpuBar');
            const ramBar = document.getElementById('ramBar');
            const diskBar = document.getElementById('diskBar');

            if (cpu) cpu.textContent = `${cpuVal}%`;
            if (ram) ram.textContent = `${ramVal}%`;
            if (disk) disk.textContent = `${diskVal}%`;
            if (cpuBar) cpuBar.style.width = `${cpuVal}%`;
            if (ramBar) ramBar.style.width = `${ramVal}%`;
            if (diskBar) diskBar.style.width = `${diskVal}%`;
        }
    } catch (e) {
        console.error('Failed to load system status:', e);
    }
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
        'web-search': 'Search the web for: ',
        'weather': 'What is the weather in ',
        'add-expense': 'Add expense: $',
        'pomodoro': 'Start a pomodoro for: ',
        'log-habit': 'Log habit: ',
        'daily-summary': 'Give me my daily productivity summary',
    };
    const input = document.getElementById('messageInput');
    if(input) {
        input.value = prompts[action] || '';
        input.focus();
        if (action === 'daily-summary') sendMessage();
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
    // Apply saved settings
    setTheme(settings.theme);
    applySettings();
    updateGreeting();
    updateMood();

    // Load chat history
    loadChatHistory();

    // Add personalised welcome
    addMessage('assistant', getWelcomeMessage());

    // Connect & load data
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

    // Update greeting every minute
    setInterval(updateGreeting, 60000);

    // Refresh system stats every 30 seconds
    setInterval(loadSystemStatus, 30000);
});
