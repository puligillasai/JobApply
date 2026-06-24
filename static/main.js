// static/js/main.js - The frontend conversation manager

document.getElementById('runSearchBtn').addEventListener('click', async () => {
    const resultsContainer = document.getElementById('resultsContainer');
    runSearchBtn.textContent = 'Searching...';
    
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

    } catch (error) {
        console.error("Search failed:", error);
        alert("Could not connect to the agent server. Try again later.");
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

    } catch (error) {
        console.error("Research failed:", error);
        alert("Could not connect to the agent server. Try again later.");
    } finally {
        researchBtn.textContent = '🔬 Research Role'; // Reset button state
    }
});

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
                    <a href="${job.link}" target="_blank" class="btn primary">Apply Now &rarr;</a>
                </div>
            </div>`;
        container.innerHTML += jobCardHtml;
    });
}

