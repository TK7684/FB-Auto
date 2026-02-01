# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

D Plus Skin Facebook AI Bot - An AI-powered bot that handles customer inquiries via Messenger DMs and Facebook page comments. Uses Gemini API for Thai language responses, ChromaDB for semantic product search, and implements conservative rate limiting to avoid Facebook API bans.

**Tech Stack**: FastAPI, Gemini AI (free tier), ChromaDB, Sentence Transformers, Facebook Graph API

---

## Running the Application

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing
```bash
# Run all tests
pytest tests/

# Test API endpoints
python scripts/test_api.py

# Test knowledge base search
python -c "from services.knowledge_base import KnowledgeBase; kb = KnowledgeBase(); print(kb.search('ฝ้า'))"
```

---

## Architecture

### Application Flow
1. **Startup** (`main.py:lifespan`) - Initializes services in order: RateLimiter → KnowledgeBase → GeminiService → FacebookService
2. **Webhook** (`api/webhooks.py`) - Receives Facebook events (GET for verification, POST for messages/comments)
3. **Processing** - Background tasks handle non-blocking response generation
4. **Response** - Uses semantic search + Gemini AI for Thai responses

### Service Layer

**KnowledgeBase** (`services/knowledge_base.py`)
- ChromaDB with sentence-transformer embeddings (supports Thai)
- Two collections: `products` (from CSV) and `qa_pairs` (from scraped posts)
- CSV must have columns: `Product_Name`, `Symptom_Target`, `Price`, `Promotion`, `Link`, `Description`

**FacebookService** (`services/facebook_service.py`)
- Wraps Graph API with automatic retry on retryable errors
- Integrates with RateLimiter for all outbound calls
- Supports DMs and private comment replies

**GeminiService** (`services/gemini_service.py`)
- Generates Thai responses using `gemini-pro`
- Special handling for "ฝ้า" (melasma) queries via keyword detection
- Falls back to template responses on API failure

**RateLimiter** (`services/rate_limiter.py`)
- Token Bucket (per-second) + Sliding Window (hourly)
- **Critical**: Limits set to 85% of Facebook's actual limits for safety
- Never modify these upward without understanding Facebook's policies

### Configuration (`config/settings.py`)

Uses pydantic-settings for type-safe environment variable loading:

**Required Environment Variables:**
- `GEMINI_API_KEY` - From Google AI Studio
- `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`
- `FACEBOOK_WEBHOOK_VERIFY_TOKEN` - Random string for webhook verification

**Feature Flags:**
- `ENABLE_DM_REPLIES` - Enable Messenger DM responses (default: true)
- `ENABLE_COMMENT_REPLIES` - Enable page comment replies (default: true)
- `ENABLE_AUTO_SCRAPE` - Auto-scrape posts for knowledge base (default: false)

### Global Service Instances

Services are initialized once at startup and stored as globals in `main.py`:
- `rate_limiter`, `knowledge_base`, `facebook_service`, `gemini_service`

All service modules provide `get_*()` factory functions that return these globals.

---

## Product Data

The bot loads products from `data/products.csv` on startup. Required columns:
- `Product_Name` - Product name
- `Symptom_Target` - Thai symptoms/conditions (e.g., "ฝ้า รอยดำ")
- `Price` - Price (numeric or string)
- `Promotion` - Current promotion text
- `Link` - Product URL (Shopee, website, etc.)
- `Description` - Product description

---

## Webhook Setup

1. Create a public URL (Cloudflare Tunnel, ngrok, etc.)
2. Configure webhook in Meta Developer Portal
3. Subscribe to: `messages`, `feed`, `comments`
4. Set verify token to match `FACEBOOK_WEBHOOK_VERIFY_TOKEN`

**Scripts available:**
- `scripts/setup_webhook.py` - Automated webhook setup via Graph API
- `scripts/test_webhook.py` - Test webhook functionality
- `scripts/scrape_facebook.py` - Scrape historical posts for knowledge base

---

## Special Features

### "ฝ้า" (Melasma) Handling

The bot detects "ฝ้า" keywords and provides specialized responses:
- Explains causes (hormonal, sun, medication)
- Recommends products with effective ingredients
- Emphasizes sunscreen use and realistic timeline (4-8 weeks)

See `services/gemini_service.py` for the melasma prompt and `config/constants.py` for related constants.

### Rate Limits

Conservative limits (85% of actual Facebook limits):

| Type | Limit | Safety Margin |
|------|-------|---------------|
| Messenger Send (text) | 300/sec actual | 250/sec |
| Messenger Send (media) | 10/sec actual | 8/sec |
| Page API | Variable | 100/sec |
| Private Replies | 750/hour actual | 700/hour |

Monitor metrics at `/health/metrics`

---

## Monitoring & Logs

- Health checks: `/health`, `/health/ready`, `/health/live`
- Rate limit metrics: `/health/metrics`
- Configuration: `/health/config` (sanitized, no secrets)
- Logs: `logs/app.log`, `logs/errors.log`, `logs/rate_limits.log`

---

## Important Notes

- **Rate Limits**: Never increase rate limits - they're set to 85% for safety
- **Thai Language**: All responses and prompts are in Thai
- **ChromaDB**: Vector store persists to `./data/knowledge_base/`
- **Fallback Responses**: Bot uses template responses if Gemini API fails
