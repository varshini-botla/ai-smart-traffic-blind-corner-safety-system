# Local Setup & Execution Guide

## Prerequisites
- **Python**: 3.10+ (Tested on Python 3.12.3)
- **Node.js**: v18+ (Tested on Node.js v22.14.0, npm 10.9.2)

---

## 1. Quick Start Instructions

### Terminal 1: Backend Service
From the project root:
```powershell
# 1. Install backend dependencies
pip install -r requirements.txt

# 2. Retrain/verify AI model (optional - model is pre-trained)
python ai/train_model.py

# 3. Start FastAPI server
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API will be accessible at:
- **API URL**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`
- **WebSocket Stream**: `ws://127.0.0.1:8000/ws/traffic`

---

### Terminal 2: React Frontend Dashboard
In a second terminal:
```powershell
cd frontend
npm install
npm run dev
```
Frontend Web Dashboard will be accessible at:
- **URL**: `http://localhost:5173`

---

## 2. Running Automated Tests
Run the entire 36-test suite:
```powershell
python -m pytest backend/tests/ tests/ -v
```

---

## 3. Retraining and Evaluating the AI Model
```powershell
# Generate dataset
python ai/dataset/generate_dataset.py

# Train Random Forest Classifier
python ai/train_model.py

# Display evaluation metrics & confusion matrix
python ai/evaluate_model.py
```
