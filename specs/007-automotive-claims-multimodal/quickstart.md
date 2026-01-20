# Quickstart: Automotive Claims Multimodal Processing

**Feature**: 007-automotive-claims-multimodal  
**Date**: 2026-01-20

---

## One-Command Setup (Recommended)

Run the automated setup script to configure everything:

```powershell
# From project root directory
.\scripts\setup_automotive_claims.ps1 -StartServers
```

This script will:
- ✅ Validate your environment (Python, Node.js, .env)
- ✅ Install Python dependencies
- ✅ Create Azure Content Understanding analyzers
- ✅ Index claims policies for RAG
- ✅ Initialize database tables
- ✅ Install frontend dependencies
- ✅ Start API and frontend servers
- ✅ Open browser to http://localhost:3000

### Script Options

```powershell
# Full setup and start servers
.\scripts\setup_automotive_claims.ps1 -StartServers

# Skip Azure analyzer setup (if already configured)
.\scripts\setup_automotive_claims.ps1 -SkipAzureSetup -StartServers

# Verify environment without making changes
.\scripts\setup_automotive_claims.ps1 -VerifyOnly

# Setup only, don't start servers
.\scripts\setup_automotive_claims.ps1
```

---

## Prerequisites

Before running the setup script, ensure you have:

1. **Azure Subscription** with Content Understanding resource
2. **Azure OpenAI** deployment with `text-embedding-3-small` model
3. **Python 3.10+** and **Node.js 18+** installed
4. **`.env` file** with required settings (copy from `.env.example`)

### Required Environment Variables

```bash
# Azure Content Understanding
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_CONTENT_UNDERSTANDING_API_KEY=your-api-key

# Azure OpenAI (for embeddings)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Automotive Claims (optional - has defaults)
AUTO_CLAIMS_ENABLED=true
AUTO_CLAIMS_POLICIES_PATH=data/automotive-claims-policies.json
```

---

## Manual Setup Steps

If you prefer manual setup or the script fails, follow these steps:

### 1. Install Dependencies

```powershell
# Python dependencies
uv sync
# or: pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Create Azure Analyzers

```powershell
python scripts/setup_automotive_analyzers.py --create-all
python scripts/setup_automotive_analyzers.py --verify
```

### 3. Index Claims Policies

```powershell
python scripts/index_claims_policies.py
```

### 4. Start Servers

```powershell
# Option A: Use the launcher script
.\scripts\run_frontend.bat

# Option B: Start manually in separate terminals
# Terminal 1 - API
uv run python -m uvicorn api_server:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Open Browser

- **Frontend**: http://localhost:3000
- **Admin View**: http://localhost:3000/admin  
- **API Docs**: http://localhost:8000/docs

---

## Database Tables

Tables are created automatically on first API request using `CREATE TABLE IF NOT EXISTS`.
No manual migration is needed.

Tables created:
- `claim_media` - Uploaded files and analysis results
- `claim_keyframes` - Video keyframes
- `claim_damage_areas` - Detected damage from images
- `claim_repair_items` - Parsed repair estimates
- `claim_policy_chunks` - RAG policy embeddings
- `claim_assessments` - AI assessment results

### Verify Tables (Optional)

```sql
-- Connect to PostgreSQL and run:
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE 'claim%';
```

---

## UI Testing Workflow

Once servers are running:

### 1. Admin View - Create & Upload

1. Navigate to **http://localhost:3000/admin**
2. Select **"Automotive Claims"** from persona dropdown
3. Click **"Create Application"**
4. Upload test files (images, video, PDFs)
5. Click **"Process"** to run multimodal analysis

### 2. Claims Adjuster View - Review

1. Click on application to open detail view
2. Review **Evidence Gallery** (images, video keyframes)
3. Review **Damage Assessment** with AI severity ratings
4. Review **Policy Citations** explaining recommendations
5. Make adjuster decision: Approve / Adjust / Deny

### 3. Ask IQ - Policy Questions

Try questions like:
- "What is the severity rating for front bumper damage?"
- "When should I refer a claim to SIU?"
- "What factors indicate potential fraud?"

---

## API Endpoints Reference

```bash
# Claims Media
GET /api/claims/{app_id}/media
GET /api/claims/{app_id}/media/{media_id}/damage-areas
GET /api/claims/{app_id}/media/{media_id}/keyframes

# Claims Assessment
GET /api/claims/{app_id}/assessment
POST /api/claims/{app_id}/assessment/decision

# Process
POST /api/claims/{app_id}/process
```

Full API docs: http://localhost:8000/docs

---

## Running Tests

```powershell
# All automotive claims tests
pytest tests/test_auto_claims_*.py -v

# Specific phase
pytest tests/test_auto_claims_phase1_config.py -v
pytest tests/test_auto_claims_phase5_policy_engine.py -v
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Analyzer not found" | `python scripts/setup_automotive_analyzers.py --create-all` |
| "Video processing timeout" | Use clips under 5 minutes |
| "No policy results" | `python scripts/index_claims_policies.py` |
| "Database connection error" | Check PostgreSQL settings in `.env` |
| "Port already in use" | Kill existing processes on 8000/3000 |

---

## Quick Reference

```powershell
# Full setup + start
.\scripts\setup_automotive_claims.ps1 -StartServers

# Just start servers
.\scripts\run_frontend.bat

# Re-index policies
python scripts/index_claims_policies.py

# Run all tests
pytest tests/test_auto_claims_*.py -v
```
