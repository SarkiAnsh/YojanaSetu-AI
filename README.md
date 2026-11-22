# 🪔 YojanaSetu AI | योजना सेतु AI

> **[DEMO] Bilingual AI welfare scheme eligibility checker — built for Indian hackathon**
>
> ⚠️ This uses demo data. Not connected to any government system. Verify at official portals.

---

## What It Does

YojanaSetu AI helps Indian citizens find out which government welfare schemes they may qualify for — in **Hindi or English** — using voice or text.

**Current demo covers 5 schemes:**
1. PM Kisan Samman Nidhi (पीएम किसान)
2. Ayushman Bharat – PMJAY (आयुष्मान भारत)
3. PM Awas Yojana – Gramin (पीएम आवास ग्रामीण)
4. National Scholarship Portal (राष्ट्रीय छात्रवृत्ति)
5. Indira Gandhi Widow Pension – IGNWPS (विधवा पेंशन)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Tailwind CSS + Vite |
| Backend | Python FastAPI |
| Database | Supabase (PostgreSQL) |
| Voice | Web Speech API (browser built-in) |

---

## Running Locally

### Conversational AI provider

The question order, answer parsing, scheme data, and eligibility decisions remain
rule-based. The optional `/api/chat` endpoint only explains the current question.
The default configuration uses local Ollama in offline mode:

```env
AI_PROVIDER=ollama
OFFLINE_MODE=true
OLLAMA_CHAT_URL=http://127.0.0.1:11434/api/chat
OLLAMA_MODEL=gemma4:e2b
```

Confirm the model is installed with `ollama list`. If Ollama is not already
running, start it with `ollama serve`. To use the existing Gemini provider instead,
set `OFFLINE_MODE=false` and `AI_PROVIDER=gemini`, then configure
`GEMINI_API_KEY` in `backend/.env`. Offline mode always uses Ollama and never
falls back to a cloud provider.

### 1. Backend (FastAPI)

```bash
cd backend

# Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
copy .env.example .env
# Edit .env with your Gemini API key (optional for Phase 1)

# Start the server
uvicorn main:app --reload
# → Running at http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### 2. Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
# → Running at http://localhost:5173
```

### 3. Open in browser
Go to: **http://localhost:5173**

---

## Project Structure

```
scheme-saathi/
├── frontend/        # React app
├── backend/         # FastAPI server
│   ├── data/        # [DEMO] scheme data
│   ├── services/    # Eligibility logic, Q&A flow
│   └── main.py      # API routes
├── supabase/        # Database schema (Phase 3)
└── docs/            # Data sources reference
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Server status |
| GET | `/api/schemes` | List all demo schemes |
| POST | `/api/next-question` | Get next Q&A question |
| POST | `/api/chat` | Clarify the current rule-based question |
| POST | `/api/check-eligibility` | Run full eligibility check |

**Interactive API docs:** http://localhost:8000/docs

---

## Privacy & Disclaimers

- ✅ No Aadhaar, PAN, or bank details collected
- ✅ No data stored without explicit user consent
- ✅ Not connected to any government database or portal
- ⚠️ Demo data only — verify at official government portals
- ⚠️ Not legal advice — consult official sources

---

## Roadmap

- **Phase 1** (current): Core eligibility checker, voice input
- **Phase 2**: Voice polish, better Hindi support, document checklists  
- **Phase 3**: User accounts, consent-based profile storage
- **Phase 4**: Personalized scheme notifications
- **Phase 5**: Application status dashboard
- **Phase 6**: Grievance assistant

---

*Built with ❤️ for Indian citizens | Hackathon Demo Project*
