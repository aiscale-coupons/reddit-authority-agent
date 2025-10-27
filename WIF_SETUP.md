# Workload Identity Federation Setup Guide

This guide walks you through setting up Workload Identity Federation (WIF) to securely authenticate your Reddit Authority Agent running on Vercel with Google Cloud Firestore, without storing service account keys.

## What is Workload Identity Federation?

Workload Identity Federation allows applications running outside Google Cloud (like on Vercel) to access Google Cloud resources by exchanging external credentials (like OIDC tokens) for temporary Google Cloud credentials. This eliminates the need to store and manage long-lived service account keys.

**Benefits:**
- No long-lived keys to manage or rotate
- Automatic credential expiration and refresh
- Better audit trails
- Compliance with security best practices

## Prerequisites

- Google Cloud Project with Firestore enabled
- Vercel project deployed
- `gcloud` CLI installed locally
- Organization/Project-level permissions to manage IAM and workload identity pools

## Step 1: Enable Required APIs

First, enable the necessary Google Cloud APIs:

```bash
# Set your Google Cloud Project ID
export PROJECT_ID="your-google-cloud-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Enable required APIs
gcloud services enable iamcredentials.googleapis.com \
  --project=$PROJECT_ID

gcloud services enable sts.googleapis.com \
  --project=$PROJECT_ID

gcloud services enable cloudresourcemanager.googleapis.com \
  --project=$PROJECT_ID

gcloud services enable iam.googleapis.com \
  --project=$PROJECT_ID
```

## Step 2: Create a Workload Identity Pool

A workload identity pool is a container for external identities.

```bash
# Create the workload identity pool
gcloud iam workload-identity-pools create "vercel-pool" \
  --project=$PROJECT_ID \
  --location="global" \
  --display-name="Vercel Workload Pool"

# Get the pool resource name
export WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe "vercel-pool" \
  --project=$PROJECT_ID \
  --location="global" \
  --format='value(name)')

echo "Workload Identity Pool ID: $WORKLOAD_IDENTITY_POOL_ID"
```

## Step 3: Create a Workload Identity Provider

The provider configures how to validate external tokens (in this case, from Vercel).

```bash
# Create the workload identity provider
gcloud iam workload-identity-pools providers create-oidc "vercel-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="vercel-pool" \
  --display-name="Vercel Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.environment=assertion.environment" \
  --issuer-uri="https://vercel.com" \
  --attribute-condition="assertion.aud == '$PROJECT_ID'"

# Get the provider resource name
export WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers describe "vercel-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="vercel-pool" \
  --format='value(name)')

echo "Workload Identity Provider: $WORKLOAD_IDENTITY_PROVIDER"
```

## Step 4: Create a Service Account

Create a service account that will be used by your Vercel application:

```bash
# Create the service account
gcloud iam service-accounts create reddit-authority-agent \
  --project=$PROJECT_ID \
  --display-name="Reddit Authority Agent Service Account"

# Get the service account email
export SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts describe reddit-authority-agent \
  --project=$PROJECT_ID \
  --format='value(email)')

echo "Service Account Email: $SERVICE_ACCOUNT_EMAIL"
```

## Step 5: Grant Firestore Permissions

Grant the service account permission to access Firestore:

```bash
# Grant Firestore Admin role (or use a more restrictive role if needed)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/datastore.user"

# Or for Firestore in Native mode:
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/firestore.admin"
```

## Step 6: Create Service Account Impersonation Binding

This allows the external identity (Vercel) to impersonate the service account:

```bash
# Create the impersonation binding
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --principal="principalSet://goog/subject/${WORKLOAD_IDENTITY_PROVIDER##*/providers/vercel-provider}"
```

## Step 7: Configure Vercel Environment Variables

Add the following environment variables to your Vercel project:

1. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**

2. Add these variables:

```
GOOGLE_CLOUD_PROJECT = your-google-cloud-project-id
WORKLOAD_IDENTITY_PROVIDER = projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/vercel-pool/providers/vercel-provider
SERVICE_ACCOUNT_EMAIL = reddit-authority-agent@your-project-id.iam.gserviceaccount.com
```

Replace:
- `your-google-cloud-project-id` with your actual project ID
- `PROJECT_NUMBER` with your project number (from Step 1)
- `reddit-authority-agent@your-project-id.iam.gserviceaccount.com` with the actual service account email

## Step 8: Update Application Code

Update your Flask application to use Workload Identity Federation. Modify `api/agent.py`:

```python
import os
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import firestore

def initialize_firestore_with_wif():
    """
    Initializes Firestore using Workload Identity Federation.
    This method works with external identities (like Vercel).
    """
    try:
        # Get credentials using Application Default Credentials (ADC)
        # In Vercel environment with WIF, this will automatically use the
        # workload identity credentials
        credentials, project_id = google.auth.default()
        
        # If running locally without WIF, you can use:
        # credentials, project_id = google.auth.default(
        #     scopes=['https://www.googleapis.com/auth/cloud-platform']
        # )
        
        db = firestore.Client(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            credentials=credentials
        )
        logger.info("Connected to Firestore using Workload Identity Federation.")
        return db
    except Exception as e:
        logger.error(f"Error initializing Firestore with WIF: {e}")
        return None
```

Replace the `initialize_firestore()` function in your code with the above implementation.

## Step 9: Update vercel.json

Update your `vercel.json` to include the new environment variables:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/agent.py",
      "use": "@vercel/python"
    },
    {
      "src": "public/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/agent.py"
    },
    {
      "src": "/(.*)",
      "dest": "public/$1"
    }
  ],
  "env": {
    "REDDIT_CLIENT_ID": "@reddit_client_id",
    "REDDIT_CLIENT_SECRET": "@reddit_client_secret",
    "REDDIT_USERNAME": "@reddit_username",
    "REDDIT_REFRESH_TOKEN": "@reddit_refresh_token",
    "GOOGLE_CLOUD_PROJECT": "@google_cloud_project",
    "WORKLOAD_IDENTITY_PROVIDER": "@workload_identity_provider",
    "SERVICE_ACCOUNT_EMAIL": "@service_account_email",
    "APP_ID": "@app_id",
    "API_KEY": "@api_key"
  }
}
```

## Step 10: Deploy to Vercel

Commit your changes and push to GitHub:

```bash
git add api/agent.py vercel.json
git commit -m "Configure Workload Identity Federation for Firestore access"
git push origin main
```

Vercel will automatically redeploy your application with the new configuration.

## Step 11: Test the Deployment

Once deployed, test the endpoints:

```bash
# Health check (no auth required)
curl https://your-vercel-domain.vercel.app/api/health

# Get posts (requires API key)
curl -H "X-API-Key: your_api_key" \
  https://your-vercel-domain.vercel.app/api/posts

# Trigger agent cycle (requires API key)
curl -X POST \
  -H "X-API-Key: your_api_key" \
  https://your-vercel-domain.vercel.app/api/run-agent
```

## Troubleshooting

### Error: "Permission denied" when accessing Firestore

**Cause**: The service account doesn't have the required permissions.

**Solution**:
```bash
# Verify the role is assigned
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format='table(bindings.role)' \
  --filter="bindings.members:$SERVICE_ACCOUNT_EMAIL"

# Re-grant the role if needed
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/firestore.admin"
```

### Error: "Invalid credential" or "Unauthorized"

**Cause**: The workload identity provider or impersonation binding is not configured correctly.

**Solution**:
1. Verify the provider exists:
   ```bash
   gcloud iam workload-identity-pools providers list \
     --project=$PROJECT_ID \
     --workload-identity-pool="vercel-pool"
   ```

2. Verify the impersonation binding:
   ```bash
   gcloud iam service-accounts get-iam-policy $SERVICE_ACCOUNT_EMAIL \
     --project=$PROJECT_ID
   ```

### Error: "Workload identity pool not found"

**Cause**: The pool or provider resource name is incorrect.

**Solution**:
1. List all pools:
   ```bash
   gcloud iam workload-identity-pools list \
     --project=$PROJECT_ID \
     --location="global"
   ```

2. List all providers:
   ```bash
   gcloud iam workload-identity-pools providers list \
     --project=$PROJECT_ID \
     --workload-identity-pool="vercel-pool" \
     --location="global"
   ```

3. Update environment variables with correct values.

## Cleanup (if needed)

To remove the workload identity setup:

```bash
# Delete the provider
gcloud iam workload-identity-pools providers delete "vercel-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="vercel-pool"

# Delete the pool
gcloud iam workload-identity-pools delete "vercel-pool" \
  --project=$PROJECT_ID \
  --location="global"

# Delete the service account
gcloud iam service-accounts delete $SERVICE_ACCOUNT_EMAIL \
  --project=$PROJECT_ID
```

## Security Best Practices

1. **Principle of Least Privilege**: Use the most restrictive role possible
   - Use `roles/datastore.user` instead of `roles/firestore.admin` if only read/write access is needed
   - Create custom roles for specific operations if needed

2. **Audit Logging**: Enable Cloud Audit Logs to track all API calls
   ```bash
   gcloud logging sinks create firestore-audit \
     logging.googleapis.com/projects/$PROJECT_ID/logs/cloudaudit.googleapis.com \
     --log-filter='resource.type="cloud_firestore" AND protoPayload.authenticationInfo.principalEmail="'$SERVICE_ACCOUNT_EMAIL'"'
   ```

3. **Monitor Access**: Set up alerts for suspicious activity
   - Use Cloud Monitoring to track Firestore access patterns
   - Set up notifications for unusual access

4. **Rotate Credentials**: While WIF doesn't use long-lived keys, credentials are automatically rotated by Google Cloud

5. **Network Security**: Consider using VPC Service Controls to restrict access to Firestore

## Advanced Configuration

### Multiple Environments

For different environments (dev, staging, prod), create separate:
- Workload identity pools
- Service accounts with appropriate roles
- Vercel projects with environment-specific variables

### Custom Roles

For more granular control, create custom roles:

```bash
gcloud iam roles create redditAgentFirestore \
  --project=$PROJECT_ID \
  --title="Reddit Agent Firestore Access" \
  --description="Custom role for Reddit Authority Agent Firestore access" \
  --permissions=datastore.entities.get,datastore.entities.list,datastore.entities.update,datastore.entities.create
```

### Conditional Access

Restrict access based on conditions:

```bash
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --principal="principalSet://goog/subject/${WORKLOAD_IDENTITY_PROVIDER##*/providers/vercel-provider}" \
  --condition='resource.matchTag("env", "prod")'
```

## References

- [Google Cloud Workload Identity Federation Documentation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Workload Identity Federation Setup Guide](https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)
- [Firestore Authentication](https://cloud.google.com/firestore/docs/auth)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)

## Next Steps

1. Complete the setup steps above
2. Update your application code
3. Deploy to Vercel
4. Monitor the logs for any issues
5. Set up alerts and monitoring
6. Document your setup for team members

