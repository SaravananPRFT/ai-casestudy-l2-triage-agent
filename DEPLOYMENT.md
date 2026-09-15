# Deployment Guide — NorthPeak Order Triage Agent

This guide covers four ways to deploy the agent. Each section is self-contained.

---

## Option 1 — Streamlit Community Cloud (Recommended · Free)

**Best for:** sharing the Streamlit UI publicly with zero infrastructure.

### Prerequisites
- GitHub account (repo already pushed: `SaravananPRFT/ai-casestudy-l2-triage-agent`)
- Anthropic API key

### Steps

1. **Go to** https://share.streamlit.io and sign in with your GitHub account.

2. **Click** "New app" (top-right).

3. **Fill in the deploy form:**
   - Repository: `SaravananPRFT/ai-casestudy-l2-triage-agent`
   - Branch: `main`
   - Main file path: `ui/app.py`

4. **Open "Advanced settings"** → click the **Secrets** tab and paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   Replace the value with your actual key. This is stored encrypted — never put it in code.

5. **Click "Deploy"**. Streamlit Cloud will install dependencies from `requirements.txt` automatically and give you a public URL like:
   ```
   https://saravananprft-ai-casestudy-l2-triage-agent-uiapp-xxxx.streamlit.app
   ```

6. **Verify** — open the URL, navigate to "🎯 Triage a Ticket", pick a sample ticket, and click **▶ Run Triage**.

### Notes
- Every push to `main` triggers an automatic redeploy.
- Free tier allows 1 private app; public apps are unlimited.
- No cold starts — app stays warm while it has visitors.

---

## Option 2 — Render (Free · Sleeps on inactivity)

**Best for:** exposing the app as a web service with slightly more control.

### Prerequisites
- Render account at https://render.com (free tier)
- GitHub repo connected

### Steps

1. **Log in** to https://render.com → click **"New +"** → **"Web Service"**.

2. **Connect your GitHub repo** `SaravananPRFT/ai-casestudy-l2-triage-agent`.

3. **Configure the service:**
   | Field | Value |
   |---|---|
   | Name | `northpeak-triage-agent` |
   | Region | Pick closest to you |
   | Branch | `main` |
   | Runtime | `Python 3` |
   | Build command | `pip install -r requirements.txt` |
   | Start command | `streamlit run ui/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
   | Instance type | **Free** |

4. **Add environment variable:**
   - Click **"Advanced"** → **"Add Environment Variable"**
   - Key: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-...`

5. **Click "Create Web Service"**. First deploy takes ~3 minutes.

6. **Verify** at the Render-provided URL (e.g. `https://northpeak-triage-agent.onrender.com`).

### Notes
- Free tier **spins down after 15 minutes of inactivity** — first request after sleep takes ~30 seconds.
- Upgrade to Starter ($7/month) to keep it always-on.

---

## Option 3 — Hugging Face Spaces (Free · ML-friendly)

**Best for:** sharing AI/ML demos with the HuggingFace community.

### Prerequisites
- HuggingFace account at https://huggingface.co
- `huggingface_hub` CLI or web UI

### Steps

1. **Go to** https://huggingface.co/new-space.

2. **Configure the Space:**
   - Owner: your HF username
   - Space name: `northpeak-order-triage`
   - License: MIT
   - SDK: **Streamlit**
   - Hardware: **CPU Basic (free)**

3. **Click "Create Space"**. HuggingFace creates a git repo for the Space.

4. **Add your project files** — clone the Space repo and copy in the project:
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/northpeak-order-triage
   cd northpeak-order-triage
   # Copy your project files in
   cp -r <path-to-project>/* .
   git add .
   git commit -m "Initial deploy"
   git push
   ```

5. **Add the API key secret:**
   - Go to your Space → **Settings** → **Repository secrets**
   - Add: `ANTHROPIC_API_KEY` = `sk-ant-...`
   - In `ui/app.py` the `load_dotenv` call will pick it up automatically via the environment.

6. **Verify** — HuggingFace shows a build log; once green, the app is live at:
   ```
   https://huggingface.co/spaces/<your-username>/northpeak-order-triage
   ```

### Notes
- Spaces are **public by default** — anyone can see and use the app.
- Upgrade to a private Space ($9/month) if you need access control.
- Cold starts are rare but possible if the Space is paused due to inactivity.

---

## Option 4 — Azure Container Apps (Enterprise · Free tier available)

**Best for:** Azure-native deployments with Azure AD / PKCE authentication.

This option includes the **PKCE OAuth 2.0 flow** (Azure AD) so only authorised users can access the app.

### Prerequisites
- Azure account (free tier: $200 credit for 30 days, then pay-as-you-go)
- Azure CLI installed: `winget install Microsoft.AzureCLI`
- Docker Desktop installed
- Azure Container Registry (or Docker Hub)

### Part A — Containerise the app

1. **Create `Dockerfile`** in the project root:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "ui/app.py", \
        "--server.port=8501", \
        "--server.address=0.0.0.0", \
        "--server.headless=true"]
   ```

2. **Build and test locally:**
   ```bash
   docker build -t northpeak-triage .
   docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-ant-... northpeak-triage
   # Open http://localhost:8501 to verify
   ```

### Part B — Push to Azure Container Registry

3. **Login and create registry:**
   ```bash
   az login
   az group create --name northpeak-rg --location eastus
   az acr create --resource-group northpeak-rg --name northpeakacr --sku Basic
   az acr login --name northpeakacr
   ```

4. **Tag and push the image:**
   ```bash
   docker tag northpeak-triage northpeakacr.azurecr.io/northpeak-triage:latest
   docker push northpeakacr.azurecr.io/northpeak-triage:latest
   ```

### Part C — Deploy to Azure Container Apps

5. **Create the Container App:**
   ```bash
   az containerapp env create \
     --name northpeak-env \
     --resource-group northpeak-rg \
     --location eastus

   az containerapp create \
     --name northpeak-triage \
     --resource-group northpeak-rg \
     --environment northpeak-env \
     --image northpeakacr.azurecr.io/northpeak-triage:latest \
     --registry-server northpeakacr.azurecr.io \
     --target-port 8501 \
     --ingress external \
     --env-vars ANTHROPIC_API_KEY=secretref:anthropic-key \
     --secrets anthropic-key=sk-ant-...
   ```

6. **Get the public URL:**
   ```bash
   az containerapp show \
     --name northpeak-triage \
     --resource-group northpeak-rg \
     --query properties.configuration.ingress.fqdn -o tsv
   ```

### Part D — Add Azure AD / PKCE Authentication (optional)

7. **Register an app in Azure AD:**
   - Go to **Azure Portal** → **Azure Active Directory** → **App registrations** → **New registration**
   - Name: `NorthPeak Triage Agent`
   - Redirect URI: `https://<your-container-app-url>/callback`
   - Note the **Application (client) ID** and **Directory (tenant) ID**

8. **Enable Container Apps Authentication:**
   ```bash
   az containerapp auth microsoft update \
     --name northpeak-triage \
     --resource-group northpeak-rg \
     --client-id <app-client-id> \
     --tenant-id <tenant-id> \
     --client-secret <app-secret>
   ```

   This enforces the **PKCE flow** automatically — Azure AD handles the full OAuth 2.0 exchange (steps 1–8 in the PKCE diagram) before the user ever reaches your app.

9. **Verify** — navigating to the app URL now redirects to Azure AD login first.

### Notes
- Free tier: 180,000 vCPU-seconds and 360,000 GiB-seconds per month.
- Scale to zero when idle (no charges when not in use).
- PKCE auth is only needed if you want to restrict access to specific Azure AD users/groups.

---

## Quick Comparison

| | Streamlit Cloud | Render | HuggingFace | Azure Container Apps |
|---|---|---|---|---|
| Cost | Free | Free (sleeps) | Free | Free tier / pay-as-you-go |
| Setup time | 5 min | 10 min | 15 min | 45–60 min |
| Custom domain | No (free tier) | No (free tier) | No (free tier) | Yes |
| Auth / SSO | No | No | No | Yes (Azure AD / PKCE) |
| Always-on | Yes | No | Sometimes | Yes (scale-to-zero) |
| Best for | Demos / capstone | Dev testing | ML community | Enterprise / production |
| **Recommendation** | **Start here** | Optional | Optional | If Azure AD required |
