# Sentinel Finance OS 🛡️

**Sentinel Finance OS (PerkPe)** is a smart financial co-pilot designed to optimize your spending and rewards. It sits on top of your payment apps to ensure every transaction maximizes your Effective Realized Value (ERV).

## 🚀 Key Features
- **Arbitrator Agent**: Orchestrates specialist agents to evaluate "Financial Winning Moves."
- **PgVector Integration**: Uses AlloyDB for semantic intent filtering (e.g., "Mute travel offers").
- **Specialist Ecosystem**: Modular agents for Travel, Lifestyle, Utility, and Shopping.
- **FastAPI Backend**: High-performance API serving the dashboard and handling automation triggers.

## 🛠️ Technology Stack
- **Languages**: Python 3.11
- **Frameworks**: FastAPI, Uvicorn, Pydantic
- **GCP Services**: Cloud Run, AlloyDB, Vertex AI, Secret Manager
- **Database**: AlloyDB (PostgreSQL) with `pgvector`

## ☁️ Deployment to GCP Cloud Run

### 1. Prerequisites
- A GCP Project with Billing enabled.
- APIs enabled: `run.googleapis.com`, `alloydb.googleapis.com`, `secretmanager.googleapis.com`, `aiplatform.googleapis.com`.
- A [Serverless VPC Access Connector](https://cloud.google.com/run/docs/configuring/connecting-vpc) named `sentinel-vpc-connector`.

### 2. Configuration
- Ensure a secret named `sentinel_db_password` exists in Secret Manager.
- Update `service.yaml` and `deploy.sh` with your `GCP_PROJECT_ID`.

### 3. Execution
Run the automated deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```

## 💻 Local Development
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   uvicorn src.api.server:app --reload
   ```

---
*Note: In production, it is recommended to serve static files via Cloud CDN or a dedicated Nginx sidecar.*
