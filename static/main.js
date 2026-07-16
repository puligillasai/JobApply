// static/js/main.js - The frontend conversation manager

const STATUS_COLORS = {
    not_applied: '#64748b',
    applied: '#10b981',
    in_progress: '#f59e0b',
    needs_attention: '#ef4444'
};

const STATUS_LABELS = {
    not_applied: 'Not Applied',
    applied: '✓ Applied',
    in_progress: '⏳ In Progress',
    needs_attention: '⚠️ Needs Attention'
};

let autoRefreshInterval = null;
let currentCustomRole = null;

const runSearchBtn = document.getElementById('runSearchBtn');
const researchBtn = document.getElementById('researchBtn');
const customRoleInput = document.getElementById('customRoleInput');

document.getElementById('selectAllPortals').addEventListener('click', () => {
    document.querySelectorAll('.portal-checkbox input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = true;
    });
});

document.getElementById('deselectAllPortals').addEventListener('click', () => {
    document.querySelectorAll('.portal-checkbox input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
});

runSearchBtn.addEventListener('click', async () => {
    runSearchBtn.textContent = 'Searching...';
    stopAutoRefresh();
    updateSearchStatus('Searching for: DevOps Engineer, SRE, Cloud Engineer');
    currentCustomRole = null;

    try {
        const jobsData = await searchJobs({ portals: getSelectedPortals() });
        displayJobs(jobsData);
        updateLastUpdated();
        updateSearchStatus(`Found ${jobsData.length} jobs`);
        startAutoRefresh();
    } catch (error) {
        console.error('Search failed:', error);
        alert(error.message || 'Could not connect to the agent server. Try again later.');
        updateSearchStatus('Search failed');
    } finally {
        runSearchBtn.textContent = '🔍 Run Advanced Search';
    }
});

researchBtn.addEventListener('click', async () => {
    const customRole = customRoleInput.value.trim();

    if (!customRole) {
        alert('Please enter a role to research');
        return;
    }

    researchBtn.textContent = 'Researching...';
    currentCustomRole = customRole;
    stopAutoRefresh();
    updateSearchStatus(`Searching for: ${customRole}`);
    document.getElementById('currentSearchRole').textContent = `Searching: ${customRole} (USA)`;

    try {
        const jobsData = await searchJobs({
            custom_role: customRole,
            portals: getSelectedPortals()
        });
        displayJobs(jobsData);
        updateLastUpdated();
        updateSearchStatus(`Found ${jobsData.length} jobs for ${customRole}`);
        startAutoRefresh();
    } catch (error) {
        console.error('Research failed:', error);
        alert(error.message || 'Could not connect to the agent server. Try again later.');
        updateSearchStatus('Research failed');
    } finally {
        researchBtn.textContent = '🔬 Research Role';
    }
});

document.getElementById('refreshInterval').addEventListener('change', event => {
    const interval = parseInt(event.target.value, 10);
    if (Number.isNaN(interval)) {
        stopAutoRefresh();
    } else {
        startAutoRefresh(interval);
    }
});

document.getElementById('stopRefreshBtn').addEventListener('click', () => {
    stopAutoRefresh();
    document.getElementById('refreshInterval').value = 'manual';
});

function getSelectedPortals() {
    return Array.from(document.querySelectorAll('.portal-checkbox input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.value);
}

async function searchJobs(payload) {
    if (!payload.portals || payload.portals.length === 0) {
        throw new Error('Please select at least one supported job portal.');
    }

    const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    const responseBody = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(responseBody.error || 'Search request failed.');
    }

    return Array.isArray(responseBody) ? responseBody : [];
}

function startAutoRefresh(intervalSeconds = null) {
    stopAutoRefresh();

    const intervalSelect = document.getElementById('refreshInterval');
    const interval = intervalSeconds || parseInt(intervalSelect.value, 10);

    if (Number.isNaN(interval) || interval <= 0) {
        return;
    }

    document.getElementById('stopRefreshBtn').style.display = 'inline-block';

    autoRefreshInterval = setInterval(async () => {
        try {
            const payload = { portals: getSelectedPortals() };
            if (currentCustomRole) {
                payload.custom_role = currentCustomRole;
            }

            const jobsData = await searchJobs(payload);
            displayJobs(jobsData);
            updateLastUpdated();
        } catch (error) {
            console.error('Auto-refresh failed:', error);
        }
    }, interval * 1000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    document.getElementById('stopRefreshBtn').style.display = 'none';
}

function updateLastUpdated() {
    const now = new Date();
    document.getElementById('lastUpdated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

function updateSearchStatus(status) {
    document.getElementById('searchStatus').textContent = status;
}

function displayJobs(jobsArray) {
    const container = document.getElementById('resultsContainer');
    container.replaceChildren();

    if (!Array.isArray(jobsArray) || jobsArray.length === 0) {
        const message = document.createElement('p');
        message.className = 'hidden-message';
        message.textContent = 'No matching jobs found in the last 24 hours based on your criteria.';
        container.appendChild(message);
        return;
    }

    jobsArray.forEach(job => {
        container.appendChild(createJobCard(job));
    });
}

function createJobCard(job) {
    const confidenceClass = getConfidenceClass(job.confidence);
    const matchPercentage = Number(job.match_percentage) || 0;
    const matchColor = matchPercentage >= 70 ? '#10b981' : matchPercentage >= 50 ? '#f59e0b' : '#ef4444';
    const jobId = buildJobId(job);
    const appStatus = STATUS_LABELS[localStorage.getItem(jobId)] ? localStorage.getItem(jobId) : 'not_applied';

    const card = document.createElement('div');
    card.className = `job-card ${confidenceClass}`;
    card.dataset.jobId = jobId;

    const statusTag = document.createElement('span');
    statusTag.className = 'status-tag';
    statusTag.textContent = job.confidence || 'Low Confidence';
    card.appendChild(statusTag);

    const match = document.createElement('div');
    match.className = 'match-percentage';
    match.style.color = matchColor;
    match.textContent = `🎯 ${matchPercentage}% Match`;
    card.appendChild(match);

    card.appendChild(createApplicationStatus(jobId, appStatus));

    const title = document.createElement('h3');
    title.textContent = job.title || 'Untitled role';
    card.appendChild(title);

    const company = document.createElement('p');
    company.className = 'company-tag';
    company.textContent = job.company || 'Unknown company';
    card.appendChild(company);

    const details = document.createElement('div');
    details.className = 'details';
    details.appendChild(createDetail('📍 Location:', job.location || 'Not specified'));
    details.appendChild(createDetail('📅 Posted:', job.posted_date || 'Recently'));
    details.appendChild(createDetail('🌐 Source:', job.source || 'Unknown'));
    details.appendChild(createApplyLink(job.link, jobId, 'Apply Now →'));
    details.appendChild(createRawLink(job.link, jobId));
    card.appendChild(details);

    return card;
}

function createApplicationStatus(jobId, appStatus) {
    const wrapper = document.createElement('div');
    wrapper.className = 'application-status';

    const label = document.createElement('label');
    label.textContent = 'Application Status:';
    wrapper.appendChild(label);

    const select = document.createElement('select');
    select.className = 'status-select';
    Object.keys(STATUS_LABELS).forEach(status => {
        const option = document.createElement('option');
        option.value = status;
        option.textContent = STATUS_LABELS[status];
        option.selected = status === appStatus;
        select.appendChild(option);
    });
    select.addEventListener('change', event => updateApplicationStatus(jobId, event.target.value));
    wrapper.appendChild(select);

    const badge = document.createElement('span');
    badge.className = 'status-badge';
    badge.style.background = STATUS_COLORS[appStatus];
    badge.textContent = STATUS_LABELS[appStatus];
    wrapper.appendChild(badge);

    return wrapper;
}

function createDetail(labelText, valueText) {
    const detail = document.createElement('p');
    const label = document.createElement('strong');
    label.textContent = `${labelText} `;
    detail.appendChild(label);
    detail.append(document.createTextNode(valueText));
    return detail;
}

function createApplyLink(rawUrl, jobId, text) {
    const link = document.createElement('a');
    link.href = sanitizeUrl(rawUrl);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'btn primary apply-link';
    link.textContent = text;
    link.addEventListener('click', () => markAsApplied(jobId));
    return link;
}

function createRawLink(rawUrl, jobId) {
    const paragraph = document.createElement('p');
    paragraph.className = 'raw-link';
    paragraph.append('🔗 ');

    const link = document.createElement('a');
    link.href = sanitizeUrl(rawUrl);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = link.href === window.location.href ? '#' : link.href;
    link.addEventListener('click', () => markAsApplied(jobId));
    paragraph.appendChild(link);

    return paragraph;
}

function sanitizeUrl(rawUrl) {
    if (!rawUrl || rawUrl === '#') {
        return '#';
    }

    try {
        const url = new URL(rawUrl, window.location.origin);
        return ['http:', 'https:'].includes(url.protocol) ? url.href : '#';
    } catch {
        return '#';
    }
}

function getConfidenceClass(confidence) {
    if (confidence === 'High Confidence') {
        return 'high-confidence';
    }
    if (confidence === 'Medium Confidence') {
        return 'medium-confidence';
    }
    return 'low-confidence';
}

function buildJobId(job) {
    const parts = [job.company || 'unknown', job.title || 'untitled', job.link || ''];
    return `job_${encodeURIComponent(parts.join('|')).slice(0, 180)}`;
}

function findJobCard(jobId) {
    return Array.from(document.querySelectorAll('.job-card'))
        .find(card => card.dataset.jobId === jobId);
}

function updateApplicationStatus(jobId, status) {
    if (!STATUS_LABELS[status]) {
        return;
    }

    localStorage.setItem(jobId, status);
    const jobCard = findJobCard(jobId);
    if (!jobCard) {
        return;
    }

    const statusBadge = jobCard.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.style.background = STATUS_COLORS[status];
        statusBadge.textContent = STATUS_LABELS[status];
    }

    const applyLink = jobCard.querySelector('.apply-link');
    if (applyLink) {
        applyLink.style.background = status === 'not_applied' ? '' : STATUS_COLORS[status];
        applyLink.textContent = status === 'not_applied' ? 'Apply Now →' : STATUS_LABELS[status];
    }
}

function markAsApplied(jobId) {
    updateApplicationStatus(jobId, 'applied');
}
