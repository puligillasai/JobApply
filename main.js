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
            // Optionally send search parameters here: body: JSON.stringify({ role: 'SRE' })
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
        runSearchBtn.textContent = 'Run Search'; // Reset button state
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
        const jobCardHtml = `
            <div class="job-card high-confidence"> 
                <span class="status-tag">${job.confidence}</span>
                <h2>${job.title}</h2>
                <p>Company: ${job.company}</p>
                <a href="${job.link}" class="btn primary">View Job Link</a>
            </div>`;
        container.innerHTML += jobCardHtml;
    });
}

