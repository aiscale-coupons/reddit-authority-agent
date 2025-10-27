# Vercel Deployment Setup Guide

This guide provides step-by-step instructions to deploy the Reddit Authority Agent to Vercel.

## Quick Start

### Step 1: Go to Vercel Dashboard

1. Visit https://vercel.com/dashboard
2. Sign in with your GitHub account (or create one if needed)

### Step 2: Import GitHub Repository

1. Click **"Add New..."** → **"Project"**
2. Click **"Import Git Repository"**
3. Search for and select **`reddit-authority-agent`** from your repositories
4. Click **"Import"**

### Step 3: Configure Project Settings

When the import dialog appears:

- **Project Name**: `reddit-authority-agent` (or your preferred name)
- **Framework Preset**: Select **"Other"** (since it's a Python Flask app)
- **Root Directory**: Leave as default (`.`)
- Click **"Continue"**

### Step 4: Add Environment Variables

In the **"Environment Variables"** section, add the following variables:



**To add environment variables:**

1. Click in the **"Environment Variables"** input field
2. Enter the variable name
3. Enter the variable value
4. Click **"Add"** to add more variables
5. Repeat for all variables above

### Step 5: Deploy

1. Click **"Deploy"**
2. Wait for the deployment to complete (typically 2-3 minutes)
3. Once complete, you'll see a success message with your deployment URL

## Post-Deployment Configuration

### Step 1: Verify Deployment

Once deployment is complete:

1. Click the **"Visit"** button or go to your deployment URL
2. You should see the Review Console interface
3. Test the health endpoint: `https://your-domain.vercel.app/api/health`

### Step 2: Configure Google Cloud Firestore Access

For the application to access Firestore, you need to set up authentication:

#### Option A: Using Service Account Key (Recommended)

1. **Create a Service Account in Google Cloud:**
   - Go to https://console.cloud.google.com/
   - Navigate to **"Service Accounts"** (under IAM & Admin)
   - Click **"Create Service Account"**
   - Name: `reddit-authority-agent`
   - Click **"Create and Continue"**

2. **Grant Firestore Permissions:**
   - Click **"Continue"** on the next screen
   - Click **"Grant this service account access to the project"**
   - Select role: **"Cloud Datastore User"** or **"Firestore Admin"**
   - Click **"Continue"**

3. **Create and Download Key:**
   - Click **"Create Key"**
   - Choose **"JSON"** format
   - Click **"Create"**
   - The key file will download automatically

4. **Add to Vercel:**
   - Open the downloaded JSON key file
   - Copy its entire contents
   - In Vercel project settings → Environment Variables
   - Add a new variable: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
   - Paste the entire JSON content as the value
   - Click **"Save"**
   - Redeploy the project

#### Option B: Using Application Default Credentials

If you have `gcloud` CLI set up locally:

```bash
gcloud auth application-default login
```

This creates credentials that Vercel can use automatically.

### Step 3: Test API Endpoints

Once Firestore is configured, test the API:

```bash
# Health check
curl https://your-domain.vercel.app/api/health

# Get all posts (requires API key)
curl -H "X-API-Key: your_api_key" \
  https://your-domain.vercel.app/api/posts

# Trigger agent cycle (requires API key)
curl -X POST \
  -H "X-API-Key: your_api_key" \
  https://your-domain.vercel.app/api/run-agent
```

## Environment Variables Reference

### Reddit Configuration

- **REDDIT_CLIENT_ID**: Your Reddit app's client ID
  - Found at: https://www.reddit.com/prefs/apps
  
- **REDDIT_CLIENT_SECRET**: Your Reddit app's client secret
  - Found at: https://www.reddit.com/prefs/apps

- **REDDIT_USERNAME**: Your Reddit account username
  - The account that created the Reddit app

- **REDDIT_REFRESH_TOKEN**: OAuth refresh token for authentication
  - More secure than storing passwords
  - Can be generated using PRAW with your credentials

### Google Cloud Configuration

- **GOOGLE_CLOUD_PROJECT**: Your Google Cloud Project ID
  - Found at: https://console.cloud.google.com/
  - Format: `project-id` or `project-id-12345`

- **GOOGLE_APPLICATION_CREDENTIALS_JSON**: Service account key (JSON)
  - The entire JSON content from your service account key file
  - Required for Firestore access

### Application Configuration

- **APP_ID**: Unique identifier for your application instance
  - Used in Firestore collection paths
  - Example: `reddit-authority-agent-prod`

- **SUBREDDIT_NAME**: (Optional) The subreddit to monitor
  - Default: `test_automation_jobs`
  - Set only if you want to override the default

- **API_KEY**: Secure API key for endpoint authentication
  - Generate with: `openssl rand -hex 32`
  - Used in `X-API-Key` header for API requests

## Troubleshooting

### Deployment Fails

**Error**: `Build failed`

**Solution**:
1. Check the build logs in Vercel dashboard
2. Ensure `requirements.txt` contains all dependencies
3. Verify Python version compatibility (Vercel uses Python 3.9+)

### 500 Error on API Endpoints

**Error**: `Internal Server Error`

**Solution**:
1. Check Vercel logs: Click **"Deployments"** → **"Logs"**
2. Common causes:
   - Missing environment variables
   - Invalid Google Cloud credentials
   - Reddit API connection issues

### Firestore Connection Fails

**Error**: `Could not initialize Firestore`

**Solution**:
1. Verify `GOOGLE_CLOUD_PROJECT` is correct
2. Ensure service account has Firestore permissions
3. Check that `GOOGLE_APPLICATION_CREDENTIALS_JSON` is properly set
4. Verify Firestore is enabled in your Google Cloud project

### Reddit Connection Fails

**Error**: `Failed to connect to Reddit`

**Solution**:
1. Verify credentials:
   ```bash
   # Check Client ID and Secret at:
   https://www.reddit.com/prefs/apps
   ```
2. Ensure Refresh Token is valid:
   - Tokens expire if not used for 6 months
   - Regenerate if needed
3. Verify app type is "Confidential" (not "Installed")

## Monitoring and Logs

### View Deployment Logs

1. Go to Vercel Dashboard
2. Select your project
3. Click **"Deployments"**
4. Click on a deployment
5. Click **"Logs"** tab

### View Runtime Logs

1. Click **"Functions"** tab
2. Select the `api/agent.py` function
3. View real-time logs

### Set Up Error Tracking

Consider integrating error tracking services:
- **Sentry**: For error monitoring
- **LogRocket**: For session replay and debugging
- **Datadog**: For comprehensive monitoring

## Advanced Configuration

### Custom Domain

1. Go to project settings → **"Domains"**
2. Click **"Add"**
3. Enter your custom domain
4. Follow DNS configuration instructions

### Scheduled Agent Cycles

To run the agent automatically on a schedule:

1. Update `vercel.json`:
   ```json
   {
     "crons": [
       {
         "path": "/api/run-agent",
         "schedule": "0 */6 * * *"
       }
     ]
   }
   ```

2. Deploy the changes:
   ```bash
   git add vercel.json
   git commit -m "Add scheduled agent cycles"
   git push
   ```

### Environment-Specific Configuration

For different environments (dev, staging, prod):

1. Create separate Vercel projects
2. Or use environment variables to control behavior:
   ```python
   ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
   ```

## Security Best Practices

1. **Rotate API Keys**: Change `API_KEY` periodically
2. **Secure Credentials**: Never commit `.env` files
3. **Use HTTPS**: All Vercel deployments use HTTPS by default
4. **Monitor Access**: Review Vercel logs for suspicious activity
5. **Limit Permissions**: Use least-privilege for service accounts
6. **Audit Logs**: Enable Google Cloud audit logging

## Next Steps

After successful deployment:

1. **Configure Monitoring**: Set up error tracking and alerting
2. **Implement Logging**: Add structured logging for debugging
3. **Add Analytics**: Track API usage and performance
4. **Plan Scaling**: Design for increased load if needed
5. **Set Up CI/CD**: Automate testing and deployment

## Support

For issues:
1. Check Vercel documentation: https://vercel.com/docs
2. Check PRAW documentation: https://praw.readthedocs.io/
3. Check Firestore documentation: https://firebase.google.com/docs/firestore
4. Open an issue on GitHub

## Additional Resources

- [Vercel Python Documentation](https://vercel.com/docs/functions/python)
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Flask Documentation](https://flask.palletsprojects.com/)

