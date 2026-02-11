# D Plus Skin Facebook AI Bot

AI-powered Facebook bot for D Plus Skin skincare business. The bot answers customer questions about products, provides recommendations, and handles both DMs and page comments automatically.

## 🏗️ System Architecture: The "Two-Bot" System

To ensure 100% reliability and compliance with Facebook's policies, the system runs two separate bots simultaneously:

### 1. The Operator (`dplus_bot_api`)
- **Role**: Instant Responder (Real-time)
- **Channel**: Facebook Messenger (DMs)
- **Mechanism**: **Webhooks**. Facebook pushes messages to the bot instantly via a secure **Cloudflare Tunnel**.
- **Speed**: < 3 seconds
- **Status**: Exposed to Public Internet (via Tunnel)

### 2. The Sweeper (`dplus_cleanup_worker`)
- **Role**: Comment Manager (Scheduled)
- **Channel**: Facebook Page Comments
- **Mechanism**: **Polling**. The bot wakes up every **60 minutes**, scans the last 50 posts for unreplied comments, answers them, and then goes back to sleep.
- **Why?**: This "slow" approach is safer for comments and prevents "Spam" flags from Facebook.
- **Status**: Private (No Internet Exposure needed)

---

## 🚀 Features

- 🤖 **AI-Powered Responses** - Uses Gemini API (Flash 2.0) for natural Thai language responses
- 📊 **Google Sheets Logging** - Logs all Chats and Comments to a shared Google Sheet in real-time
- 📚 **Knowledge Base** - Semantic search using ChromaDB and sentence transformers
- 🔒 **Rate Limiting** - Built-in protection to avoid Facebook API bans
- 🌏 **Thai Language** - Specialized support for Thai skincare queries
- 🎯 **Specialized for "ฝ้า"** - Enhanced handling for melasma/blemish queries
- 🆓 **100% Free** - Uses only free services (Gemini Free Tier, Cloudflare Tunnel Free)

---

## 🛠️ Tech Stack

- **Language**: Python 3.9+
- **Framework**: FastAPI (for Webhooks) area
- **AI/LLM**: Google Gemini 2.0 Flash
- **Vector DB**: ChromaDB
- **Tunneling**: Cloudflare Tunnel (Dockerized)
- **Deployment**: Docker Compose on Ubuntu Server (`tk578`)

---

## 📊 Google Sheets Logging

The bot automatically logs activity to [Google Sheets](https://docs.google.com/spreadsheets/d/1TPv93ZxOHLqvUWcrnZhXpx1HCjhjdQkWEsSCxjO94qs/edit).

### 1. Chats Tab
Logs every direct message reply.
- **Columns**: Date/Time, User ID, User Message, Bot Reply

### 2. Comments Tab
Logs every comment reply from the "Sweeper" bot.
- **Columns**: Date/Time, Post ID, Post Caption, User Comment, Bot Reply, Link to Comment

---

## 📦 Deployment (Remote Server `tk578`)

The bot is deployed on a remote Ubuntu server using Docker Compose.

### Quick Deploy
We use a specialized PowerShell script to bundle, upload, and deploy the bot in one click:

```powershell
.\deployment\deploy_tk578.ps1
```

This script:
1. Bundles your local code (excluding junk files).
2. Uploads `bundle.tar.gz`, `.env`, and `service_account.json`.
3. SSHs into the server.
4. Builds and Restarts Docker Containers.

### Manual Commands (on Server)

```bash
# Check Status
docker ps

# View Logs (Main Bot)
docker logs -f dplus_bot_api

# View Logs (Sweeper)
docker logs -f dplus_cleanup_worker
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

- **AI**: `GEMINI_API_KEY`, `GEMINI_MODEL`
- **Facebook**: `FACEBOOK_APP_ID`, `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`
- **Tunnel**: `CLOUDFLARED_TOKEN` (Required for Remote Access)
- **Features**: `ENABLE_DM_REPLIES`, `ENABLE_COMMENT_REPLIES`

### Service Account (`service_account.json`)

Required for Google Sheets logging. This file must be present in the root directory and contains the private key for the Google Service Account.

---

## 📂 Project Structure

```
├── api/              # Webhook Endpoints (The Operator)
├── config/           # App Settings
├── data/             # Knowledge Base & Cache
├── deployment/       # Deployment Scripts
├── scripts/          # Worker Scripts (The Sweeper)
├── services/         # Core Logic (Gemini, FB, Google Sheets)
└── main.py           # Entry Point
```

---

## ⚠️ Troubleshooting

### Chat not responding?
1. Check if the Tunnel is up: `docker ps` on server.
2. Check if specific user is ignored: `utils/filters.py`.

### Comments not replying?
1. The Sweeper runs every **60 minutes**. Wait for the next cycle.
2. Check logs: `docker logs dplus_cleanup_worker`.

---

## 📈 Dashboard ("NongD")

A real-time dashboard is available to monitor all 3 bots (Comment, Chat, Post).

### Quick Start
Double-click `start_dashboard.bat` to launch the API, Monitor, and open the Dashboard automatically.

### Manual Start
1. **API**: `uvicorn main:app --reload`
2. **Monitor**: `python scripts/monitor_24_7.py`
3. **View**: http://localhost:8000/dashboard

---

Made with 💕 for D Plus Skin
