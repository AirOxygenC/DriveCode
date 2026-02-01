# DriveCode

Voice-powered coding assistant. Transform your ideas into code while driving with AI-powered development and GitHub integration.

## Features

- **Voice Interface**: Speak your ideas, DriveCode writes the code
- **AI-Powered**: Uses Gemini for code generation and ElevenLabs for speech recognition
- **GitHub Integration**: Automatic PR creation and merging
- **Agentic Workflow**: Generates code, writes tests, creates PRs, and merges—all autonomously

## Quick Start

### Prerequisites
- Node.js 18+ and Python 3.12+
- GitHub OAuth App ([Create one here](https://github.com/settings/developers))
- API Keys: Gemini, ElevenLabs

### Setup

1. **Clone and Install**
```bash
git clone <your-repo>
cd voice123

# Frontend
cd frontend
pnpm install

# Backend
cd ../backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Variables**

Create `.env` in the root directory:
```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_SECRET_ID=your_client_secret

# AI Services
GEMINI_KEY=your_gemini_key
ELEVENLABS_KEY=your_elevenlabs_key

# Flask
FLASK_SECRET_KEY=your_secret_key
FRONTEND_URL=http://localhost:3000
```

3. **Run**
```bash
# Terminal 1: Frontend
cd frontend
pnpm dev

# Terminal 2: Backend
cd backend
source venv/bin/activate
python3 run.py
```

Open [http://localhost:3000](http://localhost:3000)

## How It Works

### Voice-to-Code Pipeline

1. **Voice Input**: Click mic, speak your idea
2. **Transcription**: ElevenLabs Scribe converts speech to text
3. **Intent Analysis**: Gemini understands what you want to build
4. **File Planning**: AI determines where code should go
5. **Code Generation**: Gemini writes production-ready code
6. **Test Generation**: Automatic test creation
7. **PR Creation**: Opens pull request with code + tests
8. **Merge Confirmation**: Ask "Should I merge?" → Say "Yes, merge it"
9. **Auto-Merge**: Code goes live on main if given permission from user

### GitHub Integration

**Authentication Flow:**
```
Login → GitHub OAuth → Token → WebSocket → Backend
```

**PR Workflow:**
- Creates branch: `drivecode-{timestamp}`
- Commits code + tests
- Opens PR to `main`
- Waits for voice confirmation
- Merges if approved

**Voice Commands for Merging:**
- Approve: "yes", "merge", "approve", "go ahead", "do it"
- Reject: "no", "don't", "cancel", "stop", "wait"

### Security

- Token never stored in database (memory only)
- All changes visible via GitHub PRs
- User confirmation required for merge
- Branch isolation before merge
- Full audit trail on GitHub

## Architecture

```
Frontend (Next.js + React)
    ↓ WebSocket
Backend (Flask + SocketIO)
    ↓
├─ ElevenLabs (Speech-to-Text)
├─ Gemini (Code Generation)
└─ GitHub API (PR Management)
```

## API Services Used

- **GitHub API** (PyGithub): Repository access, PR creation/merging
- **Gemini API**: Code and test generation
- **ElevenLabs API**: Speech-to-text transcription

## Development

**Backend Structure:**
```
backend/
├── app/
│   ├── routes/          # OAuth endpoints
│   ├── services/        # AI & GitHub services
│   │   ├── gemini_service.py
│   │   ├── elevenlabs_service.py
│   │   ├── github_service.py
│   │   ├── generation_service.py
│   │   └── validation_service.py
│   └── socket_handlers.py  # WebSocket orchestrator
└── run.py
```

**Frontend Structure:**
```
frontend/
├── app/
│   └── page.tsx         # OAuth callback handler
└── components/
    └── voice-loop/
        ├── dashboard.tsx
        └── voice-interface.tsx
```