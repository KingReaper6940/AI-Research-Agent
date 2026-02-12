/**
 * DeepResearch — Research Page JavaScript
 * Connects via WebSocket for real-time research progress and renders results.
 */

let rawMarkdown = '';
let currentWebSocket = null;
let currentQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    // Get query from URL params
    const params = new URLSearchParams(window.location.search);
    const query = params.get('q');

    if (!query) {
        window.location.href = '/';
        return;
    }

    // Set query in header
    document.getElementById('researchQuery').textContent = query;
    document.title = `Researching: ${query} — DeepResearch`;

    // Start WebSocket connection
    startResearch(query);
});


function startResearch(query, isRetry = false) {
    currentQuery = query;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/research`;
    const ws = new WebSocket(wsUrl);
    currentWebSocket = ws;
    const startTime = Date.now();
    let sourceCount = 0;

    ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ query }));
        if (!isRetry) {
            addTimelineEvent('status', 'Connected. Starting research...', startTime);
        } else {
            addTimelineEvent('status', 'Retrying... Connected...', startTime);
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleEvent(data, startTime, () => { sourceCount++; return sourceCount; });
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addTimelineEvent('error', 'Connection error. Check that the server is running and your API key is configured.', Date.now());
        updateStatus('Connection Error', false);
        showRetryButton();
    };

    ws.onclose = (event) => {
        console.log('WebSocket closed', event.code, event.reason);
        if (!event.wasClean && event.code !== 1000) {
            addTimelineEvent('error', `Connection closed unexpectedly (code: ${event.code})`, Date.now());
            showRetryButton();
        }
    };
}


function handleEvent(event, startTime, incrementSources) {
    const { event_type, message, data } = event;

    switch (event_type) {
        case 'status':
            addTimelineEvent('status', message, Date.now());
            updateStatus(message);
            break;

        case 'sub_query':
            addTimelineEvent('sub_query', `🔍 "${message}"`, Date.now());
            break;

        case 'iteration':
            addTimelineEvent('iteration', `── ${message} ──`, Date.now());
            break;

        case 'source_found':
            const count = incrementSources();
            addSourceCard(data, message);
            document.getElementById('sourceCount').textContent = count;
            break;

        case 'synthesis':
            addTimelineEvent('synthesis', `✨ ${message}`, Date.now());
            updateStatus('Synthesizing report...');
            break;

        case 'complete':
            addTimelineEvent('complete', `✅ ${message}`, Date.now());
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            updateStatus(`Complete in ${elapsed}s`, false);
            break;

        case 'report':
            renderReport(data);
            break;

        case 'error':
            addTimelineEvent('error', `❌ ${message}`, Date.now());
            updateStatus('Error', false);
            break;
    }
}


function addTimelineEvent(type, message, timestamp) {
    const timeline = document.getElementById('timeline');
    const el = document.createElement('div');
    el.className = 'timeline-event';
    el.setAttribute('data-type', type);

    const time = new Date(timestamp).toLocaleTimeString('en-US', {
        hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
    });

    el.innerHTML = `
        <div class="timeline-dot-wrap">
            <div class="timeline-dot dot-${type}"></div>
        </div>
        <div class="timeline-content">
            <div class="timeline-message">${escapeHtml(message)}</div>
            <div class="timeline-time">${time}</div>
        </div>
    `;

    timeline.appendChild(el);
    // Auto-scroll to bottom
    const panel = document.querySelector('.progress-panel');
    if (panel) panel.scrollTop = panel.scrollHeight;
}


function addSourceCard(data, title) {
    const grid = document.getElementById('sourcesGrid');
    const card = document.createElement('div');
    card.className = 'source-card';

    const type = data.source_type || 'web';
    const badgeClass = type === 'academic' ? 'badge-academic' : type === 'wikipedia' ? 'badge-wikipedia' : 'badge-web';
    const credibility = data.credibility_score || 0;
    const credClass = credibility >= 0.8 ? 'cred-high' : credibility >= 0.6 ? 'cred-mid' : 'cred-low';
    const domain = data.domain || '';

    card.innerHTML = `
        <span class="source-type-badge ${badgeClass}">${type}</span>
        <div class="source-info">
            <div class="source-title">
                <a href="${escapeHtml(data.url || '#')}" target="_blank" rel="noopener">${escapeHtml(title || 'Untitled')}</a>
            </div>
            <div class="source-domain">${escapeHtml(domain)}</div>
        </div>
        <div class="source-credibility">
            <span class="cred-score ${credClass}">${(credibility * 100).toFixed(0)}%</span>
            <span class="cred-label">Trust</span>
        </div>
    `;

    grid.appendChild(card);
}


function renderReport(data) {
    const section = document.getElementById('reportSection');
    const content = document.getElementById('reportContent');

    rawMarkdown = data.markdown || '';

    // Render markdown using marked.js
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
        });
        content.innerHTML = marked.parse(rawMarkdown);
    } else {
        // Fallback: basic rendering
        content.innerHTML = `<pre style="white-space: pre-wrap;">${escapeHtml(rawMarkdown)}</pre>`;
    }

    section.style.display = 'block';
    // Smooth scroll to report
    setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
}


function copyReport() {
    if (rawMarkdown) {
        navigator.clipboard.writeText(rawMarkdown).then(() => {
            const btn = document.getElementById('copyBtn');
            const original = btn.innerHTML;
            btn.innerHTML = '✓ Copied!';
            setTimeout(() => { btn.innerHTML = original; }, 2000);
        });
    }
}


function updateStatus(message, active = true) {
    const badge = document.getElementById('statusBadge');
    if (active) {
        badge.className = 'meta-badge meta-active';
        badge.innerHTML = `<span class="pulse-dot"></span> ${escapeHtml(message)}`;
    } else {
        badge.className = 'meta-badge meta-complete';
        badge.innerHTML = escapeHtml(message);
    }
}


function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}


function showRetryButton() {
    // Display a retry button after connection or research failure.
    const existingBtn = document.getElementById('retryBtn');
    if (existingBtn) return; // Already showing

    const header = document.getElementById('researchHeader');
    const retryBtn = document.createElement('button');
    retryBtn.id = 'retryBtn';
    retryBtn.className = 'action-btn';
    retryBtn.style.marginTop = '16px';
    retryBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
        </svg>
        Retry Research
    `;
    retryBtn.onclick = () => {
        // Clear previous results
        document.getElementById('timeline').innerHTML = '';
        document.getElementById('sourcesGrid').innerHTML = '';
        document.getElementById('sourceCount').textContent = '0';
        document.getElementById('reportSection').style.display = 'none';
        retryBtn.remove();

        // Restart research
        updateStatus('Retrying...', true);
        startResearch(currentQuery, true);
    };
    header.appendChild(retryBtn);
}
