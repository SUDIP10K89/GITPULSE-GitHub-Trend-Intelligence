const API_BASE = 'https://gitpulse-github-trend-intelligence.onrender.com/api';

function showMessage(text, type = 'info') {
    const msg = document.getElementById('message');
    const status = document.getElementById('status');
    status.style.display = 'none';

    const styles = {
        success: { background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)', color: '#00ff88' },
        error: { background: 'rgba(255,82,82,0.06)', border: '1px solid rgba(255,82,82,0.2)', color: '#ff5252' },
        info: { background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.2)', color: '#00e5ff' }
    };

    const s = styles[type] || styles.info;
    Object.assign(msg.style, s);
    msg.style.display = 'block';
    msg.textContent = '> ' + text;
}

function showStatus(text, isSubscribed) {
    const msg = document.getElementById('message');
    const status = document.getElementById('status');
    
    msg.style.display = 'none';
    status.style.display = 'block';

    if (isSubscribed) {
        status.style.background = 'rgba(0,255,136,0.04)';
        status.style.borderColor = 'rgba(0,255,136,0.15)';
        document.getElementById('status-icon').textContent = '✓';
        document.getElementById('status-icon').style.color = '#00ff88';
    } else {
        status.style.background = 'rgba(0,229,255,0.04)';
        status.style.borderColor = 'rgba(0,229,255,0.15)';
        document.getElementById('status-icon').textContent = '○';
        document.getElementById('status-icon').style.color = '#00e5ff';
    }
    document.getElementById('status-text').textContent = text;
}

async function subscribe() {
    const email = document.getElementById('email').value.trim();
    if (!email) {
        showMessage('Please enter an email address', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();

        if (response.ok) {
            showStatus(`Status: active for ${email}`, true);
        } else {
            showMessage(data.detail || 'Subscription failed', 'error');
        }
    } catch (error) {
        showMessage('Unable to connect to server. Is it running?', 'error');
    }
}

async function unsubscribe() {
    const email = document.getElementById('email').value.trim();
    if (!email) {
        showMessage('Please enter an email address', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/unsubscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();

        if (response.ok) {
            if (data.was_subscribed) {
                showStatus(`Status: inactive for ${email}`, false);
            } else {
                showMessage(`Status: inactive for ${email}`, 'info');
            }
        } else {
            showMessage(data.detail || 'Unsubscription failed', 'error');
        }
    } catch (error) {
        showMessage('Unable to connect to server. Is it running?', 'error');
    }
}