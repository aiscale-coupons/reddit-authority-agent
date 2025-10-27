# Reddit Authority Agent

A serverless Reddit monitoring and content management agent built with Python, Flask, and Vercel. This application monitors a specified subreddit, ingests new posts into Firestore, and provides a web-based review console for managing and approving content drafts.

## Features

- **Reddit Integration**: Monitors subreddits and ingests new posts using PRAW
- **Firestore Backend**: Stores and manages post data with real-time updates
- **Web Review Console**: Interactive UI for reviewing, editing, and approving drafts
- **Serverless Deployment**: Runs on Vercel with minimal infrastructure overhead
- **RESTful API**: Complete API for managing posts and triggering agent cycles
- **Environment-Based Configuration**: Secure credential management via environment variables

## Project Structure

```
reddit-authority-agent/
├── api/
│   └── agent.py              # Main Flask application and API endpoints
├── public/
│   └── index.html            # Review console frontend
├── vercel.json               # Vercel deployment configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Prerequisites

Before deploying, ensure you have:

1. **Reddit API Credentials**:
   - Reddit App Client ID
   - Reddit App Client Secret
   - Reddit Username
   - Reddit Refresh Token (or password for token generation)

2. **Google Cloud Setup**:
   - Google Cloud Project with Firestore enabled
   - Service account credentials (for local development)

3. **Vercel Account**:
   - Vercel CLI installed (`npm install -g vercel`)
   - GitHub account linked to Vercel

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/reddit-authority-agent.git
cd reddit-authority-agent
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_REFRESH_TOKEN=your_refresh_token
GOOGLE_CLOUD_PROJECT=your_project_id
APP_ID=your_app_id
API_KEY=your_secure_api_key
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Google Cloud Authentication

For local development, authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

### 5. Run the Application

```bash
python api/agent.py
```

The application will be available at `http://localhost:5000`.

## API Endpoints

### Health Check

```
GET /api/health
```

Returns the service status.

### Run Agent Cycle

```
POST /api/run-agent
Headers: X-API-Key: your_api_key
```

Manually triggers the agent cycle to fetch and ingest new posts.

### Get All Posts

```
GET /api/posts
Headers: X-API-Key: your_api_key
```

Retrieves all posts from Firestore.

### Get Specific Post

```
GET /api/posts/{post_id}
Headers: X-API-Key: your_api_key
```

Retrieves a specific post by ID.

### Update Post

```
PUT /api/posts/{post_id}
Headers: X-API-Key: your_api_key
Content-Type: application/json

{
  "status": "Approved",
  "ai_draft": "Updated draft content"
}
```

Updates a post's status and draft content.

## Deployment to Vercel

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Initial commit: Reddit Authority Agent"
git push origin main
```

### 2. Deploy to Vercel

#### Option A: Using Vercel CLI

```bash
vercel
```

Follow the prompts to:
- Select the project name
- Confirm the project settings
- Set up environment variables

#### Option B: Using Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure environment variables in the Vercel dashboard
5. Deploy

### 3. Configure Environment Variables in Vercel

In the Vercel project settings, add the following environment variables:

| Variable | Value |
|----------|-------|
| `REDDIT_CLIENT_ID` | Your Reddit Client ID |
| `REDDIT_CLIENT_SECRET` | Your Reddit Client Secret |
| `REDDIT_USERNAME` | Your Reddit Username |
| `REDDIT_REFRESH_TOKEN` | Your Reddit Refresh Token |
| `GOOGLE_CLOUD_PROJECT` | Your Google Cloud Project ID |
| `APP_ID` | Your App ID |
| `API_KEY` | A secure API key for authentication |

### 4. Verify Deployment

Once deployed, test the health endpoint:

```bash
curl https://your-vercel-domain.vercel.app/api/health
```

## Firestore Collection Structure

Posts are stored in the following Firestore path:

```
artifacts/{APP_ID}/public/data/reddit_posts
```

Each post document contains:

```json
{
  "title": "Post Title",
  "body": "Post Content",
  "url": "https://reddit.com/r/subreddit/...",
  "author": "username",
  "created_utc": 1234567890,
  "status": "New",
  "analysis_result": null,
  "deployment_id": null,
  "ai_draft": "AI-generated draft content",
  "ingested_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Post Status Workflow

Posts progress through the following statuses:

- **New**: Freshly ingested from Reddit, awaiting analysis
- **AnalysisPending**: Analysis triggered, waiting for LLM response
- **Approved**: Approved by moderator, ready for deployment
- **Rejected**: Rejected by moderator
- **Deployed**: Successfully posted to the target subreddit

## Troubleshooting

### Reddit Connection Errors

**Error**: `unauthorized_client` or 401 HTTP response

**Solution**: Verify your Reddit credentials:
- Ensure the Client ID and Secret match your Reddit app settings
- Confirm the Refresh Token is valid and not expired
- Check that your Reddit app is configured as a "Confidential" app type

### Firestore Connection Errors

**Error**: `Could not initialize Firestore`

**Solution**:
- Ensure `GOOGLE_CLOUD_PROJECT` is set correctly
- For local development, run `gcloud auth application-default login`
- For Vercel, ensure your service account credentials are properly configured

### API Key Authentication

**Error**: 401 Unauthorized on API endpoints

**Solution**: Include the `X-API-Key` header with your API key:

```bash
curl -H "X-API-Key: your_api_key" https://your-domain/api/posts
```

## Security Considerations

1. **API Keys**: Always use strong, randomly generated API keys
2. **Environment Variables**: Never commit `.env` files to version control
3. **Refresh Tokens**: Keep Reddit refresh tokens secure and rotate them periodically
4. **Service Accounts**: Use Google Cloud service accounts with minimal required permissions
5. **HTTPS**: Ensure all communication is over HTTPS (enforced by Vercel)

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the maintainers.

## Roadmap

- [ ] LLM integration for automated draft generation
- [ ] Advanced filtering and search capabilities
- [ ] Scheduled agent cycles
- [ ] Multi-subreddit support
- [ ] Analytics and reporting dashboard
- [ ] Webhook integrations
- [ ] Rate limiting and quota management

## Acknowledgments

- [PRAW](https://praw.readthedocs.io/) - Python Reddit API Wrapper
- [Firebase](https://firebase.google.com/) - Real-time database and authentication
- [Vercel](https://vercel.com/) - Serverless deployment platform
- [Flask](https://flask.palletsprojects.com/) - Web framework

