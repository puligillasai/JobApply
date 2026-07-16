# app.py - The Main Server File
from flask import Flask, render_template, jsonify, request
from scraper_module import SUPPORTED_PORTALS, run_full_search

app = Flask(__name__)
MAX_CUSTOM_ROLE_LENGTH = 80

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
    
    data = request.get_json(silent=True) or {}
    custom_role = data.get('custom_role')
    selected_portals = data.get('portals')

    if custom_role is not None:
        if not isinstance(custom_role, str):
            return jsonify({"error": "custom_role must be text."}), 400
        custom_role = custom_role.strip()
        if not custom_role:
            custom_role = None
        elif len(custom_role) > MAX_CUSTOM_ROLE_LENGTH:
            return jsonify({"error": "custom_role is too long."}), 400

    if selected_portals is not None:
        if not isinstance(selected_portals, list) or not all(isinstance(portal, str) for portal in selected_portals):
            return jsonify({"error": "portals must be a list of supported portal names."}), 400
        if not selected_portals:
            return jsonify({"error": "At least one supported portal is required."}), 400

        unsupported = sorted(set(selected_portals) - set(SUPPORTED_PORTALS))
        if unsupported:
            return jsonify({
                "error": "Unsupported portals requested.",
                "unsupported_portals": unsupported,
                "supported_portals": SUPPORTED_PORTALS
            }), 400

        selected_portals = list(dict.fromkeys(selected_portals))

    # 2. Run the Agent/Scraper
    try:
        matching_jobs = run_full_search(custom_role=custom_role, portals=selected_portals) # Calling the intelligence module
    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({"error": "Internal server error during search."}), 500

    # 3. Return the structured data (The client-side JS will read this)
    return jsonify(matching_jobs)

if __name__ == '__main__':
    # When running locally for testing:
    # debug=False for security (prevents arbitrary code execution in production)
    app.run(debug=False, port=5001) 
