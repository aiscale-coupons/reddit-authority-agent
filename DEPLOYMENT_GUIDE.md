# Deployment Guide: Reddit Authority Agent to Vercel

This guide walks you through deploying the Reddit Authority Agent to Vercel with all necessary configurations.

## Prerequisites

- GitHub account with the repository pushed
- Vercel account (free tier available)
- Reddit API credentials
- Google Cloud Project with Firestore enabled

## Step 1: Prepare Your Credentials

Gather the following information before deployment:

### Reddit Credentials

1. **REDDIT_CLIENT_ID**: Your Reddit app's client ID
   - Found in your Reddit app settings at https://www.reddit.com/prefs/apps

2. **REDDIT_CLIENT_SECRET**: Your Reddit app's client secret
   - Found in your Reddit app settings

3. **REDDIT_USERNAME**: Your Reddit account username

4. **REDDIT_REFRESH_TOKEN**: Your Reddit refresh token
   - This is used instead of passwords for secure authentication
   - If you don't have one, you can generate it using PRAW with your username and password

### Google Cloud Credentials

1. **GOOGLE_CLOUD_PROJECT**: Your Google Cloud Project ID
   - Found in your Google Cloud Console

2. **Service Account Key** (for Vercel to access Firestore):
   - Go to Google Cloud Console → Service Accounts
   - Create a new service account with Firestore access
   - Generate a JSON key and keep it secure

### Application Credentials

1. **APP_ID**: A unique identifier for your application instance
   - Example: `reddit-authority-agent-prod`

2. **API_KEY**: A secure random string for API authentication
   - Generate using: `openssl rand -hex 32`

## Step 2: Set Up GitHub Repository

If you haven't already, push your code to GitHub:

```bash
cd reddit-authority-agent
git init
git add .
git commit -m "Initial commit: Reddit Authority Agent"
git branch -M main
git remote add origin https://github.com/yourusername/reddit-authority-agent.git
git push -u origin main
```

## Step 3: Deploy to Vercel

### Option A: Using Vercel Dashboard (Recommended for Beginners)

1. **Go to Vercel**: Visit https://vercel.com/dashboard

2. **Create New Project**:
   - Click "New Project"
   - Select "Import Git Repository"
   - Choose your `reddit-authority-agent` repository
   - Click "Import"

3. **Configure Project**:
   - **Project Name**: `reddit-authority-agent` (or your preferred name)
   - **Framework Preset**: Select "Other"
   - **Root Directory**: Leave as default (.)
   - Click "Continue"

4. **Add Environment Variables**:
   - In the "Environment Variables" section, add the following:

   ```
   REDDIT_CLIENT_ID = W4sJxi7iyJMIcnnt5bcDMA
   REDDIT_CLIENT_SECRET = 7siQh54ozEg3iKV_ckFJ8bxet1FyZA
   REDDIT_USERNAME = mylifemygoals
   REDDIT_REFRESH_TOKEN = 100412803-5182064102-1o9g8n81u-iI49cM4w-3T4hM7uN_yYyV
   GOOGLE_CLOUD_PROJECT = your_google_cloud_project_id
   APP_ID = reddit-authority-agent-prod
   API_KEY = (generate a secure random string)
   ```

5. **Deploy**:
   - Click "Deploy"
   - Wait for the deployment to complete (typically 2-3 minutes)

### Option B: Using Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   cd reddit-authority-agent
   vercel
   ```

4. **Follow the Prompts**:
   - Confirm project settings
   - When asked about environment variables, select "Add environment variables"
   - Enter each variable as prompted

## Step 4: Configure Google Cloud Firestore Access

For Vercel to access your Firestore database, you need to set up authentication:

### Option A: Using Application Default Credentials (Recommended)

1. **Create a Service Account**:
   - Go to Google Cloud Console
   - Navigate to "Service Accounts"
   - Click "Create Service Account"
   - Name it `reddit-authority-agent`
   - Grant it "Firestore Admin" role

2. **Create and Download Key**:
   - In the service account details, go to "Keys"
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Download the key file

3. **Encode the Key**:
   ```bash
   cat path/to/service-account-key.json | base64
   ```

4. **Add to Vercel**:
   - In Vercel project settings → Environment Variables
   - Add: `GOOGLE_APPLICATION_CREDENTIALS_JSON` with the base64-encoded key
   - Or use the Vercel integration with Google Cloud (if available)

### Option B: Using Vercel Google Cloud Integration

1. **Connect Google Cloud**:
   - In Vercel project settings, look for "Integrations"
   - Connect your Google Cloud account
   - Grant necessary permissions

## Step 5: Verify Deployment

Once deployment is complete:

1. **Check Health Endpoint**:
   ```bash
   curl https://your-vercel-domain.vercel.app/api/health
   ```

   Expected response:
   ```json
   {
     "status": "ok",
     "service": "Reddit Authority Agent",
     "timestamp": "2024-01-01T00:00:00.000000"
   }
   ```

2. **Access Review Console**:
   - Visit `https://your-vercel-domain.vercel.app/`
   - You should see the review console interface

3. **Test API Endpoints**:
   ```bash
   curl -H "X-API-Key: your_api_key" https://your-vercel-domain.vercel.app/api/posts
   ```

## Step 6: Set Up Scheduled Agent Cycles (Optional)

To run the agent automatically on a schedule, use Vercel Cron Jobs:

1. **Update vercel.json**:
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

2. **Deploy the changes**:
   ```bash
   git add vercel.json
   git commit -m "Add scheduled agent cycles"
   git push
   ```

## Step 7: Monitor and Manage

### View Logs

```bash
vercel logs reddit-authority-agent
```

### View Environment Variables

In Vercel Dashboard → Project Settings → Environment Variables

### Update Environment Variables

1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Edit or add variables as needed
5. Redeploy if necessary

## Troubleshooting

### Deployment Fails with "Module not found"

**Solution**: Ensure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 500 Error on API Endpoints

**Check Logs**:
```bash
vercel logs reddit-authority-agent --follow
```

**Common Issues**:
- Missing environment variables
- Invalid Google Cloud credentials
- Reddit API connection issues

### Firestore Connection Fails

**Verify**:
1. Google Cloud Project ID is correct
2. Service account has Firestore Admin role
3. Firestore database is enabled in Google Cloud Console

### Reddit Connection Fails

**Verify**:
1. Client ID and Secret are correct
2. Refresh Token is valid and not expired
3. Reddit app is configured as "Confidential" type
4. Username matches the account that created the app

## Performance Optimization

### Cold Start Optimization

- Vercel Python functions may have longer cold starts
- Consider using scheduled cron jobs instead of on-demand triggers
- Cache frequently accessed data

### Database Optimization

- Create Firestore indexes for common queries
- Use pagination for large result sets
- Implement caching strategies

## Security Best Practices

1. **Rotate API Keys**: Change your API_KEY periodically
2. **Secure Credentials**: Never commit sensitive data to Git
3. **Use HTTPS**: All Vercel deployments use HTTPS by default
4. **Monitor Access**: Review Vercel logs for suspicious activity
5. **Limit Permissions**: Use least-privilege principle for service accounts

## Next Steps

After successful deployment:

1. **Configure Monitoring**: Set up error tracking (Sentry, etc.)
2. **Implement Logging**: Use structured logging for better debugging
3. **Add Analytics**: Track API usage and performance
4. **Set Up Alerts**: Configure notifications for failures
5. **Plan Scaling**: Design for increased load if needed

## Support

For issues:
1. Check Vercel logs: `vercel logs reddit-authority-agent`
2. Review Google Cloud logs in Cloud Console
3. Check Reddit API status at https://reddit.statuspage.io/
4. Open an issue on GitHub

## Additional Resources

- [Vercel Python Documentation](https://vercel.com/docs/functions/python)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Flask Documentation](https://flask.palletsprojects.com/)

