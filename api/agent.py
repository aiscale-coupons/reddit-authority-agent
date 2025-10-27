"""
Reddit Authority Agent - Vercel Serverless Function Handler
This module provides HTTP endpoints for the Reddit Authority Agent.
"""

import os
import json
import logging
from enum import Enum
from datetime import datetime
import praw
from google.cloud import firestore
from google.auth.exceptions import DefaultCredentialsError
from flask import Flask, request, jsonify
from functools import wraps

# --- Configuration and Setup ---

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Constants and Environment Variables
SUBREDDIT_NAME = os.getenv("SUBREDDIT_NAME", "test_automation_jobs")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_REFRESH_TOKEN = os.getenv("REDDIT_REFRESH_TOKEN")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
APP_ID = os.getenv("APP_ID", "default-app-id")

# Define Post Statuses (The core workflow statuses)
class PostStatus(Enum):
    """Defines the current processing state of a Reddit post."""
    NEW = 'New'
    ANALYSIS_PENDING = 'AnalysisPending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    DEPLOYED = 'Deployed'


# --- Firebase and PRAW Initialization ---

def initialize_firestore():
    """Initializes and returns the Firestore client.
    
    Supports two authentication methods:
    1. Workload Identity Federation (recommended for production on Vercel)
    2. Application Default Credentials (for local development)
    """
    try:
        # Try to use Workload Identity Federation first (Vercel environment)
        if os.getenv("WORKLOAD_IDENTITY_PROVIDER"):
            import google.auth
            credentials, project_id = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            db = firestore.Client(
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                credentials=credentials
            )
            logger.info("Connected to Firestore using Workload Identity Federation (WIF).")
            return db
        else:
            # Fall back to Application Default Credentials
            db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
            logger.info("Connected to Firestore using Application Default Credentials (ADC).")
            return db
    except DefaultCredentialsError:
        logger.error("Could not initialize Firestore. Ensure GOOGLE_CLOUD_PROJECT is set and credentials are available.")
        return None
    except Exception as e:
        logger.error(f"Error initializing Firestore: {e}")
        return None


def initialize_reddit():
    """Initializes and returns the PRAW Reddit instance."""
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_REFRESH_TOKEN]):
        logger.error("Missing Reddit credentials. Ensure all REDDIT_* environment variables are set.")
        return None

    try:
        logger.info("Attempting PRAW connection verification...")
        logger.info(f"    Client ID: {REDDIT_CLIENT_ID[:8]}... (Verify against Reddit app settings)")
        logger.info(f"    Client Secret: {REDDIT_CLIENT_SECRET[:8]}... (Verify against Reddit app settings)")
        logger.info(f"    Refresh Token: {REDDIT_REFRESH_TOKEN[:8]}... (Verify token is correct and active)")

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            refresh_token=REDDIT_REFRESH_TOKEN,
            user_agent=f"AuthorityAgent by /u/{REDDIT_USERNAME}",
            oauth_url="https://www.reddit.com/api/v1/access_token",
        )
        
        # Verify connection by accessing the user object
        user_info = reddit.user.me()
        logger.info(f"Successfully connected to Reddit as user: {user_info}")
        return reddit
    except Exception as e:
        logger.error(f"Failed to connect to Reddit: {e}")
        return None


# --- Firestore Helper Functions ---

def get_firestore_collection_path():
    """Returns the public Firestore collection path for this app."""
    path = f"artifacts/{APP_ID}/public/data/reddit_posts"
    return path


def fetch_or_initialize_post(db, post_id, data):
    """
    Checks if a post exists in Firestore. If it does, returns the existing document.
    If not, creates a new document with 'New' status.
    """
    collection_ref = db.collection(get_firestore_collection_path())
    doc_ref = collection_ref.document(post_id)

    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        # Post does not exist, initialize it
        new_post_data = {
            "title": data['title'],
            "body": data['body'],
            "url": data['url'],
            "author": data['author'],
            "created_utc": data['created_utc'],
            "status": PostStatus.NEW.value,
            "analysis_result": None,
            "deployment_id": None,
            "ingested_at": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(new_post_data)
        logger.info(f"    -> Ingested new post: {data['title'][:50]}... (ID: {post_id})")
        return new_post_data


# --- Main Agent Logic ---

def run_agent_cycle(db, reddit):
    """
    The main processing loop for the Reddit Authority Agent.
    1. Looks for approved posts in Firestore and attempts to deploy them.
    2. Looks for new posts on Reddit and ingests them into Firestore.
    """
    if not reddit or not db:
        logger.error("Cannot run agent cycle: Reddit or Firestore connection failed.")
        return {"status": "error", "message": "Connection failed"}

    try:
        subreddit = reddit.subreddit(SUBREDDIT_NAME)
        collection_ref = db.collection(get_firestore_collection_path())

        logger.info("Searching for approved posts to deploy...")
        approved_posts = collection_ref.where("status", "==", PostStatus.APPROVED.value).limit(5).stream()
        approved_count = len(list(approved_posts))
        logger.info(f"Found {approved_count} 'Approved' posts.")

        logger.info("Searching for new posts to process...")
        new_posts_found = 0

        # Fetch the top 25 newest submissions in the monitoring subreddit
        for submission in subreddit.new(limit=25):
            # We only care about self-posts (text posts) that haven't been removed by a moderator
            if submission.stickied or submission.removed_by_category:
                continue

            if not submission.is_self:
                # This is a link post. We'll skip it for now.
                continue

            post_data = {
                'title': submission.title,
                'body': submission.selftext,
                'url': submission.url,
                'author': str(submission.author),
                'created_utc': submission.created_utc,
            }

            # Check Firestore for existence and initialize if new
            post_doc = fetch_or_initialize_post(db, submission.id, post_data)

            # If the document was initialized (i.e., status is 'New'), increment counter
            if post_doc['status'] == PostStatus.NEW.value:
                new_posts_found += 1

        logger.info(f"Found {new_posts_found} 'New' posts on Reddit to process.")
        return {
            "status": "success",
            "new_posts_found": new_posts_found,
            "approved_posts_count": approved_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"An error occurred during the agent cycle: {e}")
        return {"status": "error", "message": str(e)}


# --- Middleware and Utilities ---

def require_api_key(f):
    """Decorator to require API key for protected endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY')
        
        if not expected_key or api_key != expected_key:
            return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# --- API Endpoints ---

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "Reddit Authority Agent",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/api/run-agent', methods=['POST'])
@require_api_key
def run_agent():
    """Trigger the agent cycle manually."""
    db = initialize_firestore()
    reddit = initialize_reddit()

    result = run_agent_cycle(db, reddit)
    
    if result["status"] == "error":
        return jsonify(result), 500
    
    return jsonify(result), 200


@app.route('/api/posts', methods=['GET'])
@require_api_key
def get_posts():
    """Retrieve all posts from Firestore."""
    db = initialize_firestore()
    
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        collection_ref = db.collection(get_firestore_collection_path())
        docs = collection_ref.stream()
        
        posts = []
        for doc in docs:
            post_data = doc.to_dict()
            post_data['id'] = doc.id
            posts.append(post_data)
        
        return jsonify({"posts": posts, "count": len(posts)}), 200
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/posts/<post_id>', methods=['GET'])
@require_api_key
def get_post(post_id):
    """Retrieve a specific post by ID."""
    db = initialize_firestore()
    
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        doc = db.collection(get_firestore_collection_path()).document(post_id).get()
        
        if not doc.exists:
            return jsonify({"error": "Post not found"}), 404
        
        post_data = doc.to_dict()
        post_data['id'] = doc.id
        return jsonify(post_data), 200
    except Exception as e:
        logger.error(f"Error retrieving post: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/posts/<post_id>', methods=['PUT'])
@require_api_key
def update_post(post_id):
    """Update a specific post."""
    db = initialize_firestore()
    
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        data = request.get_json()
        
        # Validate status if provided
        if 'status' in data:
            valid_statuses = [status.value for status in PostStatus]
            if data['status'] not in valid_statuses:
                return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}"}), 400
        
        # Update the document
        db.collection(get_firestore_collection_path()).document(post_id).update({
            **data,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({"message": "Post updated successfully", "id": post_id}), 200
    except Exception as e:
        logger.error(f"Error updating post: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# --- Vercel Serverless Handler ---

def handler(request):
    """Vercel serverless function handler."""
    with app.app_context():
        return app.wsgi_app(request.environ, request.start_response)


# For local testing
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

