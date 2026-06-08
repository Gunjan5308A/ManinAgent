document.addEventListener('DOMContentLoaded', () => {
    const generatorForm = document.getElementById('generatorForm');
    const promptInput = document.getElementById('prompt');
    const qualitySelect = document.getElementById('quality');
    const fpsSelect = document.getElementById('fps');
    const useRagCheckbox = document.getElementById('useRag');
    const generateBtn = document.getElementById('generateBtn');
    
    const taskPulse = document.getElementById('taskPulse');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    const logTerminal = document.getElementById('logTerminal');
    
    const videoEmptyState = document.getElementById('videoEmptyState');
    const player = document.getElementById('player');
    const videoActions = document.getElementById('videoActions');
    const downloadLink = document.getElementById('downloadLink');
    const historyList = document.getElementById('historyList');

    let currentTaskId = null;
    let pollInterval = null;
    let loggedLinesCount = 0;

    // ── Helper: Append Log Line ───────────────────────────────────────────────
    function appendLog(message, type = 'log-line') {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        
        // Add timestamp or system prefix
        const time = new Date().toLocaleTimeString();
        line.innerText = `[${time}] ${message}`;
        
        logTerminal.appendChild(line);
        logTerminal.scrollTop = logTerminal.scrollHeight;
    }

    // ── Helper: Reset UI for New Task ──────────────────────────────────────────
    function resetUIForNewTask() {
        progressBar.style.width = '0%';
        progressPercent.innerText = '0%';
        progressText.innerText = 'Queuing task...';
        
        // Clear log terminal
        logTerminal.innerHTML = '';
        appendLog('Initializing new animation pipeline request...', 'system-line');
        
        // Disable generate button
        generateBtn.disabled = true;
        generateBtn.style.opacity = '0.6';
        generateBtn.querySelector('.btn-text').innerText = 'Generating...';
        
        taskPulse.className = 'pulse-indicator active';
        
        // Reset Video Player
        player.hidden = true;
        player.src = '';
        videoEmptyState.hidden = false;
        videoActions.hidden = true;
        
        loggedLinesCount = 0;
    }

    // ── Helper: Restore UI to Normal ──────────────────────────────────────────
    function restoreUIState() {
        generateBtn.disabled = false;
        generateBtn.style.opacity = '1';
        generateBtn.querySelector('.btn-text').innerText = 'Generate Animation';
        taskPulse.className = 'pulse-indicator';
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    // ── Fetch Task Status (Polling) ───────────────────────────────────────────
    async function checkTaskStatus(taskId) {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            if (!res.ok) throw new Error('Failed to fetch status');
            
            const task = await res.json();
            
            // 1. Update Progress Bar
            progressBar.style.width = `${task.progress}%`;
            progressPercent.innerText = `${task.progress}%`;
            
            if (task.status === 'queued') {
                progressText.innerText = 'In Queue...';
            } else if (task.status === 'processing') {
                progressText.innerText = 'Generating Animation Chunks...';
            }
            
            // 2. Append new logs
            if (task.logs && task.logs.length > loggedLinesCount) {
                for (let i = loggedLinesCount; i < task.logs.length; i++) {
                    const line = task.logs[i];
                    let logType = 'log-line';
                    
                    if (line.includes('Success!') || line.includes('completed')) {
                        logType = 'success-line';
                    } else if (line.includes('ERROR') || line.includes('failed') || line.includes('Exception')) {
                        logType = 'error-line';
                    } else if (line.includes('[Pipeline]') || line.includes('Decomposing') || line.includes('Starting')) {
                        logType = 'system-line';
                    }
                    
                    appendLog(line, logType);
                }
                loggedLinesCount = task.logs.length;
            }
            
            // 3. Check Task Completion / Failure
            if (task.status === 'completed') {
                progressText.innerText = 'Generation Complete!';
                appendLog('Animation compiled successfully.', 'success-line');
                
                // Load video player
                videoEmptyState.hidden = true;
                player.hidden = false;
                player.src = task.video_url;
                player.load();
                
                // Show actions
                videoActions.hidden = false;
                downloadLink.href = task.video_url;
                
                restoreUIState();
                loadHistory();
            } else if (task.status === 'failed') {
                progressText.innerText = 'Generation Failed';
                appendLog(`Error: ${task.error || 'Unknown error occurred'}`, 'error-line');
                restoreUIState();
                loadHistory();
            }
            
        } catch (err) {
            console.error(err);
            appendLog(`Error fetching status: ${err.message}`, 'error-line');
            restoreUIState();
        }
    }

    // ── Form Submission (Trigger Pipeline) ─────────────────────────────────────
    generatorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const topic = promptInput.value.trim();
        const quality = qualitySelect.value;
        const fps = fpsSelect.value;
        const useRag = useRagCheckbox.checked;

        if (!topic) return;

        resetUIForNewTask();

        try {
            const queryParams = new URLSearchParams({
                topic,
                quality,
                fps,
                use_rag: useRag
            });
            
            const res = await fetch(`/api/generate?${queryParams}`, {
                method: 'POST'
            });
            
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to start generation');
            }
            
            const data = await res.json();
            currentTaskId = data.task_id;
            
            appendLog(`Task registered. Task ID: ${currentTaskId}`, 'system-line');
            
            // Start polling status
            pollInterval = setInterval(() => {
                checkTaskStatus(currentTaskId);
            }, 2000);
            
        } catch (err) {
            appendLog(`Failed to submit request: ${err.message}`, 'error-line');
            restoreUIState();
        }
    });

    // ── Load Session History ───────────────────────────────────────────────────
    async function loadHistory() {
        try {
            const res = await fetch('/api/history');
            if (!res.ok) return;
            const tasks = await res.json();
            
            if (!tasks || tasks.length === 0) {
                historyList.innerHTML = '<div class="history-empty">No animations generated yet in this session.</div>';
                return;
            }
            
            // Render latest tasks first
            historyList.innerHTML = '';
            tasks.reverse().forEach(task => {
                const item = document.createElement('div');
                item.className = 'history-item';
                
                let badgeClass = 'text-muted';
                if (task.status === 'completed') badgeClass = 'status-label';
                else if (task.status === 'failed') badgeClass = 'error-line';
                else if (task.status === 'processing' || task.status === 'queued') badgeClass = 'text-secondary';
                
                item.innerHTML = `
                    <div class="history-info">
                        <div class="history-topic">${task.topic}</div>
                        <div class="history-meta">Status: <span class="${badgeClass}">${task.status.toUpperCase()}</span> • Progress: ${task.progress}%</div>
                    </div>
                    <div class="history-actions">
                        ${task.video_url ? `<button class="history-btn play-btn" data-url="${task.video_url}">Watch</button>` : ''}
                        ${task.video_url ? `<a href="${task.video_url}" download class="history-btn">Download</a>` : ''}
                    </div>
                `;
                
                historyList.appendChild(item);
            });
            
            // Attach event listeners to new play buttons
            document.querySelectorAll('.play-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const url = e.target.getAttribute('data-url');
                    videoEmptyState.hidden = true;
                    player.hidden = false;
                    player.src = url;
                    player.load();
                    player.play();
                    videoActions.hidden = false;
                    downloadLink.href = url;
                });
            });
            
        } catch (err) {
            console.error('Error loading history:', err);
        }
    }

    // Load history on startup
    loadHistory();
});
