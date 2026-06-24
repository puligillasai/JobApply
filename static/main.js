// static/js/main.js - The frontend conversation manager

let autoRefreshInterval = null;
let currentCustomRole = null;

document.getElementById('runSearchBtn').addEventListener('click', async () => {
    const resultsContainer = document.getElementById('resultsContainer');
    runSearchBtn.textContent = 'Searching...';
    
    // Stop auto-refresh when manual search is triggered
    stopAutoRefresh();
    
    // Update UI status
    updateSearchStatus('Searching for: DevOps Engineer, SRE, Cloud Engineer');
    currentCustomRole = null;
    
    try {
        // --- THIS IS THE CRUCIAL PART: Talking to app.py ---
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({}) // Empty body for default search
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const jobsData = await response.json(); // Receiving the JSON from app.py
        displayJobs(jobsData); // Function to render the list
        updateLastUpdated();
        updateSearchStatus(`Found ${jobsData.length} jobs`);
        startAutoRefresh(); // Restart auto-refresh after manual search

    } catch (error) {
        console.error("Search failed:", error);
        alert("Could not connect to the agent server. Try again later.");
        updateSearchStatus('Search failed');
    } finally {
        runSearchBtn.textContent = '🔍 Run Advanced Search'; // Reset button state
    }
});

// Research button for custom role search
document.getElementById('researchBtn').addEventListener('click', async () => {
    const customRoleInput = document.getElementById('customRoleInput');
    const customRole = customRoleInput.value.trim();
    const researchBtn = document.getElementById('researchBtn');
    
    if (!customRole) {
        alert('Please enter a role to research');
        return;
    }
    
    researchBtn.textContent = 'Researching...';
    currentCustomRole = customRole;
    
    // Stop auto-refresh when custom research is triggered
    stopAutoRefresh();
    
    // Update UI status
    updateSearchStatus(`Searching for: ${customRole}`);
    document.getElementById('currentSearchRole').textContent = `Searching: ${customRole} (USA)`;
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ custom_role: customRole })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const jobsData = await response.json();
        displayJobs(jobsData);
        updateLastUpdated();
        updateSearchStatus(`Found ${jobsData.length} jobs for ${customRole}`);
        startAutoRefresh(); // Restart auto-refresh after custom research

    } catch (error) {
        console.error("Research failed:", error);
        alert("Could not connect to the agent server. Try again later.");
        updateSearchStatus('Research failed');
    } finally {
        researchBtn.textContent = '🔬 Research Role'; // Reset button state
    }
});

// Auto-refresh functionality
document.getElementById('refreshInterval').addEventListener('change', (e) => {
    const interval = parseInt(e.target.value);
    if (interval === 'manual' || isNaN(interval)) {
        stopAutoRefresh();
    } else {
        startAutoRefresh(interval);
    }
});

document.getElementById('stopRefreshBtn').addEventListener('click', () => {
    stopAutoRefresh();
    document.getElementById('refreshInterval').value = 'manual';
});

function startAutoRefresh(intervalSeconds = null) {
    stopAutoRefresh(); // Clear any existing interval
    
    const intervalSelect = document.getElementById('refreshInterval');
    const interval = intervalSeconds || parseInt(intervalSelect.value);
    
    if (interval === 'manual' || isNaN(interval) || interval <= 0) {
        return;
    }
    
    console.log(`Starting auto-refresh every ${interval} seconds`);
    document.getElementById('stopRefreshBtn').style.display = 'inline-block';
    
    autoRefreshInterval = setInterval(async () => {
        console.log('Auto-refreshing...');
        try {
            const body = currentCustomRole ? JSON.stringify({ custom_role: currentCustomRole }) : JSON.stringify({});
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: body
            });

            if (response.ok) {
                const jobsData = await response.json();
                displayJobs(jobsData);
                updateLastUpdated();
            }
        } catch (error) {
            console.error("Auto-refresh failed:", error);
        }
    }, interval * 1000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('Auto-refresh stopped');
        document.getElementById('stopRefreshBtn').style.display = 'none';
    }
}

function updateLastUpdated() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('lastUpdated').textContent = `Last updated: ${timeString}`;
}

function updateSearchStatus(status) {
    document.getElementById('searchStatus').textContent = status;
}

function displayJobs(jobsArray) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = ''; // Clear previous results

    if (jobsArray.length === 0) {
        container.innerHTML = '<p class="hidden-message">No matching jobs found in the last 24 hours based on your criteria.</p>';
        return;
    }

    jobsArray.forEach(job => {
        // Dynamically build the HTML job card using the data received from the backend
        const confidenceClass = job.confidence === 'High Confidence' ? 'high-confidence' : 
                               job.confidence === 'Medium Confidence' ? 'medium-confidence' : 'low-confidence';
        const matchColor = job.match_percentage >= 70 ? '#10b981' : 
                          job.match_percentage >= 50 ? '#f59e0b' : '#ef4444';
        const jobCardHtml = `
            <div class="job-card ${confidenceClass}"> 
                <span class="status-tag">${job.confidence}</span>
                <div class="match-percentage" style="color: ${matchColor}; font-size: 1.5em; font-weight: bold; margin-bottom: 10px;">
                    🎯 ${job.match_percentage}% Match
                </div>
                <h3>${job.title}</h3>
                <p class="company-tag">${job.company}</p>
                <div class="details">
                    <p><strong>📍 Location:</strong> ${job.location || 'Not specified'}</p>
                    <p><strong>📅 Posted:</strong> ${job.posted_date || 'Recently'}</p>
                    <p><strong>🌐 Source:</strong> ${job.source || 'Unknown'}</p>
                    <a href="${job.link}" target="_blank" rel="noopener noreferrer" class="btn primary">Apply Now &rarr;</a>
                    <p class="raw-link" style="margin-top: 10px; font-size: 12px; word-break: break-all;">
                        🔗 <a href="${job.link}" target="_blank" rel="noopener noreferrer" style="color: #60a5fa;">${job.link}</a>
                    </p>
                </div>
            </div>`;
        container.innerHTML += jobCardHtml;
    });
}

