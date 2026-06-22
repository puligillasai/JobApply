# app.py - The Main Server File
from flask import Flask, render_template, jsonify, request
from scraper_module import run_full_search # Importing your agent logic

app = Flask(__name__)

# -------------------------------------------
# ROUTE 1: The initial webpage (When the user visits the site)
@app.route('/')
def home():
    # This renders index.html, which includes your CSS/JS links.
    return render_template('index.html')

# -------------------------------------------
# ROUTE 2: The Search API (When the JavaScript needs data)
@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """ Accepts criteria from the frontend and returns ranked jobs. """
    
    # 1. Get Criteria (Optional: If you add filters like 'only SRE')
    # data = request.get_json()
    # search_query = data.get('query')

    # 2. Run the Agent/Scraper
    try:
        matching_jobs = run_full_search() # Calling the intelligence module
    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({"error": "Internal server error during search."}), 500

    # 3. Return the structured data (The client-side JS will read this)
    return jsonify(matching_jobs)

if __name__ == '__main__':
    # When running locally for testing:
    app.run(debug=True) 
