# D Plus Skin Facebook AI Bot

AI-powered Facebook bot for D Plus Skin skincare business. The bot answers customer questions about products, provides recommendations, and handles both DMs and page comments automatically.

## Features

- 🤖 **AI-Powered Responses** - Uses Gemini API for natural Thai language responses
- 📚 **Knowledge Base** - Semantic search using ChromaDB and sentence transformers
- 🔒 **Rate Limiting** - Built-in protection to avoid Facebook API bans
- 💬 **Multi-Channel** - Handles both Messenger DMs and page comments
- 🌏 **Thai Language** - Specialized support for Thai skincare queries
- 🎯 **Specialized for "ฝ้า"** - Enhanced handling for melasma/blemish queries
- 📊 **Monitoring** - Health checks and metrics endpoints
- 🆓 **100% Free** - Uses only free services

## Tech Stack

- **Language**: Python 3.8+
- **Web Framework**: FastAPI
- **AI/LLM**: Gemini API (via Google or OpenRouter)
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (multilingual)
- **Facebook**: Graph API (official, free)
- **Hosting**: Cloudflare Tunnel (free)

## Installation

### 1. Clone and Setup

```bash
cd "C:\Users\ttapk\PycharmProjects\pythonProject\AI bot for FB page"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your credentials
notepad .env
```

Required environment variables:
- `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/)
- `FACEBOOK_APP_ID` - From [Meta Developers](https://developers.facebook.com/)
- `FACEBOOK_PAGE_ACCESS_TOKEN` - Generate from your Facebook app
- `FACEBOOK_PAGE_ID` - Your Facebook page ID
- `FACEBOOK_WEBHOOK_VERIFY_TOKEN` - Create a random string

Optional (for OpenRouter):
- `OPENROUTER_API_KEY` - API key from OpenRouter (uses `google/gemini-2.0-flash-001` or comparable model)

### 3. Prepare Product Data

The bot uses `data/products.csv` for product information. Update this with your actual products:

```csv
Product_Name,Symptom_Target,Price,Promotion,Link,Description
D Plus Whitening Serum,ฝ้า รอยดำ,890,Buy 2 Get 1 Free,https://shopee.link/...,Serum for whitening
```

### 4. Initialize Knowledge Base

```bash
# The bot will automatically load products on startup
# Or manually test:
python -c "from services.knowledge_base import KnowledgeBase; kb = KnowledgeBase(); print(kb.load_products_from_csv('data/products.csv'))"
```

## Running the Bot

### Development

```bash
# Start the bot
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Deployment with Cloudflare Tunnel

### 1. Install Cloudflare Tunnel

Download from: https://github.com/cloudflare/cloudflared/releases

### 2. Create Tunnel

```bash
cloudflared tunnel create dplus-skin-bot
```

### 3. Configure Tunnel

Create `config.yml`:

```yaml
tunnel: <your-tunnel-id>
credentials-file: C:\Users\ttapk\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: your-bot.your-domain.com
    service: http://localhost:8000
    path: /webhook/*
  - service: http_status:404
```

### 4. Run Tunnel

```bash
cloudflared tunnel run dplus-skin-bot
```

### 5. Configure Facebook Webhook

1. Go to [Meta Developer Portal](https://developers.facebook.com/)
2. Navigate to your app → Webhooks
3. Set webhook URL: `https://your-bot.your-domain.com/webhook`
4. Set verify token (match your `.env`)
5. Subscribe to: `messages`, `feed`, `comments`

## API Endpoints

### Webhook Endpoints

- `GET /webhook` - Verify webhook with Facebook
- `POST /webhook` - Receive Facebook events

### Health & Monitoring

- `GET /` - Bot information
- `GET /health` - Health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check
- `GET /health/metrics` - Rate limit metrics
- `GET /health/config` - Configuration info

## Testing

```bash
# Run unit tests (FastAPI TestClient)
pytest tests/ -v

# Verify OpenRouter connection
python scripts/test_openrouter.py

# Test knowledge base
python -c "from services.knowledge_base import KnowledgeBase; kb = KnowledgeBase(); print(kb.search('ฝ้า'))"
```

## Rate Limits

The bot uses conservative rate limits (85% of actual Facebook limits):

| Endpoint | Limit | Safety Margin |
|----------|-------|---------------|
| Messenger Send (text) | 300/sec | 250/sec |
| Messenger Send (media) | 10/sec | 8/sec |
| Page API | Variable | 100/sec |
| Private Replies | 750/hour | 700/hour |

**Critical**: Never modify these values upward without understanding Facebook's rate limit policies.

## Scraping Historical Data

To build the knowledge base from your past Facebook posts:

```bash
# Full scrape (all time)
python scripts/scrape_facebook.py --full --add-to-kb

# Incremental (last 7 days)
python scripts/scrape_facebook.py --days 7 --add-to-kb

# Custom page
python scripts/scrape_facebook.py --page yourpage --limit 100
```

## Special Features

### "ฝ้า" (Melasma) Handling

The bot has special handling for melasma queries:
- Explains causes (hormonal, sun, medication)
- Recommends products with effective ingredients
- Emphasizes sunscreen use
- Sets realistic expectations (4-8 weeks)
- Provides prevention tips

### Product Recommendations

When a user asks about a skin concern:
1. Searches knowledge base semantically
2. Finds top 3 matching products
3. Includes price, promotion, and links
4. Formats response naturally in Thai

## Project Structure

```
├── config/           # Configuration
├── services/         # Business logic
├── models/           # Data models
├── api/              # API endpoints
├── utils/            # Utilities
├── data/             # Data storage
├── scripts/          # Utility scripts
└── tests/            # Tests
```

## Troubleshooting

### Webhook Not Receiving Messages
- Check Facebook webhook subscription status
- Verify webhook URL is accessible
- Check VERIFY_TOKEN matches

### Rate Limit Errors
- Check `/health/metrics` for current usage
- Rate limits automatically recover
- Monitor `logs/rate_limits.log`

### Knowledge Base Not Working
- Ensure `data/products.csv` exists
- Check ChromaDB directory permissions
- Verify products loaded (check logs)

### Gemini/OpenRouter API Errors
- Verify API key in `.env`
- Check quota (Google) or credits (OpenRouter)
- Run `python scripts/test_openrouter.py` to verify connection
- Fallback responses will be used if API fails

## Monitoring

Check logs:
```bash
# All logs
tail -f logs/app.log

# Errors only
tail -f logs/errors.log

# Rate limits
tail -f logs/rate_limits.log
```

## Contributing

This is a business-critical bot. Please:
1. Test thoroughly before deploying
2. Never modify rate limits upward
3. Always use official Facebook APIs
4. Monitor logs regularly

## License

Proprietary - D Plus Skin Business

## Support

For issues, check:
1. Logs in `logs/` directory
2. `/health/metrics` endpoint
3. Meta Developer Documentation

---

Made with 💕 for D Plus Skin
