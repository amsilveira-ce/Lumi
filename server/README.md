# .env Configuration Guide for Elder Companion

This guide will help you set up your `.env` file with the correct credentials.

## Step 1: Get Your Google Cloud Project ID

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select or create a project
3. Copy the **Project ID** (not the project name)
4. Update in `.env`: `GOOGLE_CLOUD_PROJECT=your-project-id`

## Step 2: Enable Required APIs

Run these commands in Google Cloud Shell or with `gcloud` CLI:

```bash
# Set your project (replace YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Generative Language API
gcloud services enable generativelanguage.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled | grep -E 'aiplatform|generativelanguage'
```

## Step 3: Create Service Account & Download Key

### Option A: Using gcloud CLI (Recommended)

```bash
# Create service account
gcloud iam service-accounts create elder-companion-sa \
    --display-name="Elder Companion Service Account" \
    --description="Service account for Elder Companion AI agent"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:elder-companion-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create ~/elder-companion-key.json \
    --iam-account=elder-companion-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Move key to a secure location
mkdir -p ~/.config/gcloud/keys
mv ~/elder-companion-key.json ~/.config/gcloud/keys/
```

### Option B: Using Google Cloud Console

1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click **Create Service Account**
3. Name: `elder-companion-sa`
4. Grant role: **Vertex AI User**
5. Click **Done**
6. Click on the service account
7. Go to **Keys** tab
8. Click **Add Key** > **Create new key**
9. Choose **JSON** format
10. Save the downloaded file securely

## Step 4: Update .env File

Edit your `.env` file with the actual values:

```bash
# Example with real values
GOOGLE_CLOUD_PROJECT=my-ai-project-123456
GOOGLE_CLOUD_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourname/.config/gcloud/keys/elder-companion-key.json
```

**Important paths:**
- macOS/Linux: `/home/username/.config/gcloud/keys/elder-companion-key.json`
- Windows: `C:\Users\YourName\.config\gcloud\keys\elder-companion-key.json`
- Or use absolute path to wherever you saved the key

## Step 5: Verify Configuration

Test your setup:

```python
# test_config.py
import os
from dotenv import load_dotenv
from google.cloud import aiplatform

load_dotenv()

print("Testing configuration...")
print(f"Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
print(f"Region: {os.getenv('GOOGLE_CLOUD_REGION')}")
print(f"Credentials: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# Initialize Vertex AI
aiplatform.init(
    project=os.getenv('GOOGLE_CLOUD_PROJECT'),
    location=os.getenv('GOOGLE_CLOUD_REGION')
)
print("✓ Configuration successful!")
```

Run: `python test_config.py`

## Complete .env Template with Explanations

```env
# ============================================
# REQUIRED: Google Cloud Configuration
# ============================================

# Your Google Cloud Project ID (found in console header)
GOOGLE_CLOUD_PROJECT=my-project-id

# Region for Vertex AI (choose closest to your users)
# Options: us-central1, us-east1, us-west1, europe-west1, asia-east1
GOOGLE_CLOUD_REGION=us-central1

# Path to service account JSON key file (absolute path recommended)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/elder-companion-key.json

# ============================================
# REQUIRED: Vertex AI Model Settings
# ============================================

# Model to use
# Options:
#   - gemini-1.5-pro (most capable, slower, more expensive)
#   - gemini-1.5-flash (faster, cheaper, good for most tasks)
#   - gemini-1.0-pro (older, stable)
VERTEX_AI_MODEL=gemini-1.5-pro

# Model location (usually same as GOOGLE_CLOUD_REGION)
VERTEX_AI_LOCATION=us-central1

# ============================================
# OPTIONAL: Agent Configuration
# ============================================

AGENT_NAME=elder-companion
AGENT_VERSION=0.1.0

# ============================================
# OPTIONAL: MCP Server
# ============================================

MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8080

# ============================================
# OPTIONAL: Memory & Storage
# ============================================

MEMORY_BACKEND=local
MEMORY_PATH=./memory/conversations

# ============================================
# OPTIONAL: Additional AI Services
# ============================================

# Only needed if you want to use OpenAI or Anthropic models
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# ============================================
# OPTIONAL: Logging
# ============================================

# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
LOG_FILE=./logs/elder-companion.log
```

## Security Best Practices

1. **Never commit `.env` to git** - Already in `.gitignore`
2. **Use absolute paths** for `GOOGLE_APPLICATION_CREDENTIALS`
3. **Restrict key file permissions**:
   ```bash
   chmod 600 ~/.config/gcloud/keys/elder-companion-key.json
   ```
4. **Rotate keys regularly** (every 90 days recommended)
5. **Use different service accounts** for dev/staging/prod

## Troubleshooting

### Error: "Could not load credentials"
- Check the path to your key file is correct
- Use absolute path instead of relative path
- Verify the file exists: `ls -l /path/to/key.json`

### Error: "Permission denied"
- Verify service account has `roles/aiplatform.user` role
- Check IAM permissions in Google Cloud Console

### Error: "API not enabled"
- Run: `gcloud services enable aiplatform.googleapis.com`
- Wait 1-2 minutes for API to activate

### Error: "Project not found"
- Verify project ID is correct (not project name)
- Ensure project is active and billing is enabled

## Quick Start Checklist

- [ ] Created Google Cloud project
- [ ] Enabled Vertex AI API
- [ ] Enabled Generative Language API
- [ ] Created service account
- [ ] Downloaded service account key
- [ ] Updated `GOOGLE_CLOUD_PROJECT` in `.env`
- [ ] Updated `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
- [ ] Tested configuration with `python test_config.py`

## Additional Resources

- [Vertex AI Quickstart](https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [Gemini API Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)

---

Need help? Check the main README.md or open an issue on GitHub.