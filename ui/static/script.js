// NEXUS CORTEX LOGIC

// API Endpoints
const api = {
    start: '/api/start',
    stop: '/api/stop',
    status: '/api/status',
    query: '/api/query',
    activities: '/api/activities',
    focus: '/api/toggle_focus',
    dismissAlert: '/api/dismiss_alert',
    synthesis: '/api/synthesis'
};

// Global State
let isRunning = false;
let isFocusMode = false;
let activityChart = null;
let startTime = null;

// DOM Elements
const els = {
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    focusBtn: document.getElementById('focus-btn'),
    statusText: document.getElementById('status-text'),
    statusBadge: document.getElementById('status-badge'),
    alertSection: document.getElementById('alert-section'),
    alertMessage: document.getElementById('alert-message'),
    log: document.getElementById('activity-log'),
    queryInput: document.getElementById('query-input'),
    queryBtn: document.getElementById('query-btn'),
    queryResponse: document.getElementById('query-response'),
    uptime: document.getElementById('uptime'),
    memoryCount: document.getElementById('memory-count'),
    synthesisContent: document.getElementById('synthesis-content'),
    audioPulse: document.getElementById('audio-pulse')
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    try { initNeuralCanvas(); } catch(e) { console.error('Canvas error:', e); }
    try { initChart(); } catch(e) { console.error('Chart error:', e); }
    
    pollStatus();
    setInterval(pollStatus, 1000);
    setInterval(updateUptime, 1000);
    setInterval(fetchSynthesis, 15000); // Poll synthesis every 15s
});

// --- Event Listeners ---
els.startBtn.addEventListener('click', () => callApi(api.start, () => startTime = new Date()));
els.stopBtn.addEventListener('click', () => callApi(api.stop, () => startTime = null));
els.focusBtn.addEventListener('click', toggleFocus);
els.queryBtn.addEventListener('click', sendQuery);
els.queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendQuery();
});

// --- Core Logic ---

async function callApi(endpoint, callback) {
    try {
        const res = await fetch(endpoint, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            if (callback) callback(data);
            pollStatus(); // Immediate update
        }
    } catch (e) {
        console.error(`API Error (${endpoint}):`, e);
    }
}

async function toggleFocus() {
    try {
        const res = await fetch(api.focus, { method: 'POST' });
        const data = await res.json();
        updateFocusUI(data.is_focus_mode);
    } catch (e) {
        console.error('Focus Error:', e);
    }
}

async function sendQuery() {
    const query = els.queryInput.value.trim();
    if (!query) return;
    
    // Add user message to chat
    addChatMessage('user', query);
    els.queryInput.value = '';
    
    try {
        const res = await fetch(api.query, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await res.json();
        
        // Add AI response
        addChatMessage('ai', data.response);
        
    } catch (e) {
        addChatMessage('system', 'Error processing query.');
    }
}

function addChatMessage(role, text) {
    const p = document.createElement('p');
    p.className = `msg-${role}`;
    p.innerHTML = text.replace(/\n/g, '<br>');
    p.style.marginBottom = '10px';
    if (role === 'user') {
        p.style.color = '#a0a0b0';
        p.style.textAlign = 'right';
    } else if (role === 'ai') {
        p.style.color = '#fff';
    }
    els.queryResponse.appendChild(p);
    els.queryResponse.scrollTop = els.queryResponse.scrollHeight;
}

// --- Status Polling ---

async function pollStatus() {
    try {
        const res = await fetch(api.status);
        const data = await res.json();
        
        // Run State
        if (data.is_running !== isRunning) {
            isRunning = data.is_running;
            updateRunUI(isRunning);
        }
        
        // Focus State
        if (data.is_focus_mode !== isFocusMode) {
            isFocusMode = data.is_focus_mode;
            updateFocusUI(isFocusMode);
        }
        
        // Stats
        els.memoryCount.textContent = data.activity_count;
        
        // Alerts
        if (data.latest_alert) {
            showAlert(data.latest_alert);
        } else {
            els.alertSection.style.display = 'none';
        }
        
        // Refresh Lists
        fetchActivities();
        
        if (data.is_running) {
            els.audioPulse.style.display = 'block';
        } else {
            els.audioPulse.style.display = 'none';
        }
        
    } catch (e) {
        // Silent fail for polling
    }
}

function updateRunUI(running) {
    if (running) {
        els.statusText.textContent = 'ONLINE';
        els.statusBadge.classList.add('status-active');
        els.startBtn.disabled = true;
        els.stopBtn.disabled = false;
        if (!startTime) startTime = new Date();
    } else {
        els.statusText.textContent = 'OFFLINE';
        els.statusBadge.classList.remove('status-active');
        els.startBtn.disabled = false;
        els.stopBtn.disabled = true;
        startTime = null;
    }
}

function updateFocusUI(active) {
    if (active) {
        els.focusBtn.classList.add('focus-active');
        els.focusBtn.innerHTML = '<i class="fa-solid fa-bullseye"></i> Focus ON';
        document.body.style.border = '2px solid var(--accent-primary)';
    } else {
        els.focusBtn.classList.remove('focus-active');
        els.focusBtn.innerHTML = '<i class="fa-solid fa-bullseye"></i> Focus Mode';
        document.body.style.border = 'none';
    }
}

function updateUptime() {
    if (!startTime) {
        els.uptime.textContent = '0h 0m 0s';
        return;
    }
    const diff = new Date() - startTime;
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    els.uptime.textContent = `${h}h ${m}m ${s}s`;
}

// --- Synthesis ---
async function fetchSynthesis() {
    if (!isRunning) return;
    try {
        const res = await fetch(api.synthesis);
        const data = await res.json();
        renderSynthesis(data.insights);
    } catch(e) {}
}

function renderSynthesis(insights) {
    if (!insights || insights.length === 0) return;
    els.synthesisContent.innerHTML = '';
    insights.forEach(insight => {
        const div = document.createElement('div');
        div.className = 'insight-item';
        div.innerHTML = `<i class="fa-solid fa-lightbulb"></i> ${insight}`;
        els.synthesisContent.appendChild(div);
    });
}

// --- Activities & Chart ---

async function fetchActivities() {
    const res = await fetch(api.activities);
    const data = await res.json();
    renderLog(data.activities);
    updateChart(data.activities);
}

function renderLog(activities) {
    els.log.innerHTML = '';
    activities.forEach(act => {
        const div = document.createElement('div');
        div.className = 'log-item';
        
        const time = new Date(act.timestamp).toLocaleTimeString();
        let desc = act.app_name;
        
        // Try parsing analysis
        if (act.analysis && typeof act.analysis === 'string') {
            try { 
                const a = JSON.parse(act.analysis); 
                if (a.activity) desc += `: ${a.activity.substring(0, 30)}...`;
            } catch(e) {}
        } else if (act.analysis && act.analysis.activity) {
            desc += `: ${act.analysis.activity.substring(0, 30)}...`;
        }
        
        div.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-app">${desc}</span>
        `;
        els.log.appendChild(div);
    });
}

// --- Chart.js ---
function initChart() {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded');
        return;
    }
    const ctx = document.getElementById('activityChart').getContext('2d');
    
    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 242, 234, 0.5)');
    gradient.addColorStop(1, 'rgba(0, 242, 234, 0.0)');

    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cognitive Load',
                data: [],
                borderColor: '#00f2ea',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false, min: 0, max: 100 }
            },
            animation: { duration: 1000 }
        }
    });
}

function updateChart(activities) {
    if (!activityChart) return;
    
    // Mock data based on activity volume/complexity
    // In real app, we'd use embedding distance or complexity score
    const data = activities.map(() => Math.floor(Math.random() * 40) + 40); // 40-80 range
    
    const labels = activities.map(a => new Date(a.timestamp).toLocaleTimeString());
    
    activityChart.data.labels = labels.reverse();
    activityChart.data.datasets[0].data = data.reverse();
    activityChart.update();
}

// --- Neural Canvas Animation ---
function initNeuralCanvas() {
    const canvas = document.getElementById('neuralCanvas');
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    
    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    
    window.addEventListener('resize', resize);
    resize();
    
    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.size = Math.random() * 2;
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
        }
        
        draw() {
            ctx.fillStyle = 'rgba(0, 242, 234, 0.5)';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    for (let i = 0; i < 50; i++) particles.push(new Particle());
    
    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        particles.forEach(p => {
            p.update();
            p.draw();
            
            // Connect
            particles.forEach(p2 => {
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                
                if (dist < 150) {
                    ctx.strokeStyle = `rgba(0, 242, 234, ${0.1 - dist/1500})`;
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

// --- Alerts ---
function showAlert(alert) {
    els.alertSection.style.display = 'flex';
    els.alertMessage.innerHTML = `<strong>${alert.priority.toUpperCase()}:</strong> ${alert.message}`;
}

async function dismissAlert() {
    await fetch(api.dismissAlert, { method: 'POST' });
    els.alertSection.style.display = 'none';
}
