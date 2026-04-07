# Sentinel Finance OS 🛡️

**Sentinel Finance OS (PerkPe)** is an intelligent financial co-pilot built on agentic design principles. It sits on top of your payment surfaces to ensure every transaction and financial decision maximizes your **Effective Realized Value (ERV)**.

## 🚀 Key Features

- **First-Run Setup Wizard**: Zero-to-hero onboarding. Automatically scans Gmail to identify your credit cards, enriches their profiles with web data (live cashback rates & benefits), and saves them locally.
- **Product Deal Search**: Want to buy a TV? Input a product and the agents will find the absolute best base market price, apply all your saved credit cards' specific cashback rules, and highlight the mathematically best card to use.
- **Arbitrator Agent**: An overarching coordinator that runs specialist agents and filters recommendations through semantic intent filtering.
- **Specialist Ecosystem**: Modular agents focused on Travel, Lifestyle, Utility, and Shopping.

## 🛠️ Technology Stack & Dependencies

### Core Stack
- **Languages**: Python 3.11
- **Frameworks**: FastAPI, Uvicorn, Pydantic
- **AI Models**: Google Gemini (`google-genai`), `google-cloud-aiplatform`
- **Data Persistence**: SQLite (local) via `aiosqlite`, with optional AlloyDB support (`asyncpg`)

---

## ☁️ Deployment to GCP Cloud Run

To deploy Sentinel Finance OS to production on Google Cloud, you will need the specific dependencies and configurations outlined below.

### GCP Dependencies & APIs Setup
Before deploying, ensure the following APIs are activated in your Google Cloud Project:
1. `run.googleapis.com` (Cloud Run)
2. `secretmanager.googleapis.com` (Secret Manager)
3. `aiplatform.googleapis.com` (Vertex AI)
4. `gmail.googleapis.com` (Gmail API - required for inbox parsing)

### GCP Deployment Steps
1. **Secret Manager Initialization**:
   The app expects API credentials to be securely stored. Create the following secrets in GCP Secret Manager:
   - `serpapi_key` (Optional: for live web scraping)
   - *If using AlloyDB instead of SQLite:* `sentinel_db_password`

2. **Gmail OAuth Setup**:
   - Go to GCP Console -> Credentials -> Create OAuth client ID (Desktop app).
   - Download the file as `gmail_credentials.json` and place it in the root before creating your Docker image (or upload to Secret Manager).

3. **Deploy via Direct VPC Egress**:
   Use Direct VPC Egress instead of a Serverless VPC connector for faster, cheaper deployment.
   ```bash
   gcloud run deploy sentinel-finance-os \
       --source . \
       --network default \
       --subnet default \
       --vpc-egress all-traffic \
       --region us-central1 \
       --allow-unauthenticated
   ```

---

## 💻 Local Development & Run Instructions

Running Sentinel OS locally is the easiest way to test the agent logic and onboarding flow. 

### 1. Prerequisites Configuration
For the app to run locally, it needs access to your Gmail to discover your cards and Search functionality.
- Download your `gmail_credentials.json` from your GCP project and place it in the project root folder.
- *Optional:* Export your search provider key:
  ```bash
  export SERPAPI_KEY="your_serpapi_key_here"
  ```
  *(If no key is provided, the agents will elegantly fall back to realistic offline demo data).*

### 2. Python Environment Setup
We recommend using a local virtual environment.
```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate it
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# 3. Install core requirements and newly added dependencies:
pip install -r requirements.txt
```

### 3. Start the Server
Start the FastAPI server via Uvicorn. The local SQLite database (`sentinel_local.db`) will auto-initialize on startup.
```bash
# Export the Python path so the `src/` module is resolveable
export PYTHONPATH=.

# Start the server on port 8000
python3 src/api/server.py
```

### 4. Experience the App
Open your browser and navigate to:
**http://localhost:8000**

You will be greeted by the **First Run Setup Wizard**, which will walk you through scanning your Gmail, approving your detected credit cards, and dropping you straight into the AI Dashboard. From there, click **"Find Best Deal"** to witness the agents in action!
