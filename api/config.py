import os
import json
from http import HTTPStatus
from flask import Flask, jsonify, make_response

app = Flask(__name__)

@app.route('/api/config', methods=['GET'])
def get_config():
    """
    Returns the Firebase configuration as a JSON object.
    This endpoint is used by the frontend to initialize the Firebase app.
    """
    # The Firebase config is hardcoded in the environment variable for the frontend
    # We retrieve it here and serve it as a response.
    firebase_config_json = os.environ.get("FIREBASE_CONFIG_JSON")

    if not firebase_config_json:
        return make_response(
            jsonify({"error": "Firebase configuration not found in environment variables."}),
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

    try:
        # Load the JSON string from the environment variable
        config = json.loads(firebase_config_json)
        
        # Return the configuration
        return jsonify(config)

    except json.JSONDecodeError:
        return make_response(
            jsonify({"error": "Firebase configuration environment variable is not valid JSON."}),
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

if __name__ == '__main__':
    # This block is for local development only
    # Note: For Vercel deployment, the 'app' object is used directly by the runtime.
    app.run(debug=True, port=8000)
