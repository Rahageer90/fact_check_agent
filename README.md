# Fact-Check AI Agent

A sophisticated AI-powered fact-checking system built with LangChain, FastAPI, and Google Gemini API. This agent verifies factual claims by intelligently combining web search and news search results to provide evidence-based verdicts.

## 🎯 Overview

The Fact-Check AI Agent accepts user claims and performs comprehensive fact-checking by:

1. **Analyzing the claim** using advanced reasoning
2. **Searching the web** for general evidence
3. **Searching news sources** for recent authoritative information
4. **Synthesizing evidence** using Gemini AI
5. **Providing a reasoned verdict** with justification

### Verdict Classifications

- ✅ **Likely True** - Strong evidence supports the claim
- ⚠️ **Uncertain** - Mixed or insufficient evidence
- ❌ **Likely False** - Evidence contradicts the claim

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FastAPI Application                 │
│              (POST /fact-check endpoint)             │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           LangChain ReAct Agent                      │
│    (Orchestrates tool calling and reasoning)        │
└────────────┬──────────────────────────┬─────────────┘
             │                          │
    ┌────────▼─────────┐       ┌────────▼──────────┐
    │   Web Search     │       │  News Search      │
    │ (Serper API)     │       │  (NewsAPI)        │
    └────────┬─────────┘       └────────┬──────────┘
             │                          │
    ┌────────▼──────────────────────────▼──────┐
    │      Evidence Aggregation & Analysis      │
    │         (Gemini 2.0 Flash LLM)            │
    └────────┬──────────────────────────────────┘
             │
    ┌────────▼──────────────────────────────────┐
    │    Structured Verdict Response             │
    │  (Verdict + Explanation + Sources)        │
    └───────────────────────────────────────────┘
```

## 📋 Project Structure

```
fact_check_agent/
│
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── agent.py             # LangChain ReAct agent logic
│   ├── schemas.py           # Pydantic request/response models
│   └── __pycache__/
│
├── mcp_tools/
│   ├── web_search.py        # Google Serper API integration
│   ├── news_search.py       # NewsAPI integration
│   └── __pycache__/
│
├── services/
│   ├── gemini.py            # Google Gemini LLM service
│   └── __pycache__/
│
├── Documentation/           # Additional documentation
├── .env                     # Environment variables (API keys)
├── .env.example             # API keys template
├── requirements.txt         # Python dependencies
├── test.py                  # Comprehensive test suite
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- API Keys for:
  - [Google Gemini API](https://console.cloud.google.com/)
  - [Google Serper API](https://serper.dev/)
  - [NewsAPI](https://newsapi.org/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Rahageer90/fact_check_agent.git
   cd fact_check_agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   SERPAPI_API_KEY=your_serper_api_key_here
   NEWSAPI_API_KEY=your_newsapi_key_here
   ```

   Get your API keys from:
   - **Google Gemini**: https://aistudio.google.com/
   - **Google Serper**: https://serper.dev/
   - **NewsAPI**: https://newsapi.org/

### Running the Application

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Access the interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📡 API Reference

### Fact-Check Endpoint

**Endpoint:** `POST /fact-check`

**Request:**
```bash
curl -X POST "http://localhost:8000/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"claim": "OpenAI released GPT-4 in 2023."}'
```

**Request Body:**
```json
{
  "claim": "The claim to be fact-checked"
}
```

**Response (200 OK):**
```json
{
  "verdict": "Likely True",
  "explanation": "Multiple credible sources confirm that OpenAI released GPT-4 in March 2023. This was a major announcement widely covered by technology news outlets and official statements.",
  "sources": [
    {
      "title": "OpenAI Releases GPT-4",
      "url": "https://example.com/gpt4-release",
      "type": "news"
    },
    {
      "title": "GPT-4 Technical Report",
      "url": "https://example.com/gpt4-technical",
      "type": "web"
    }
  ],
  "tools_used": ["web_search", "news_search"]
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim` | string | Yes | The factual claim to verify (max 1000 chars) |

### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | string | One of: "Likely True", "Uncertain", "Likely False" |
| `explanation` | string | Detailed reasoning with evidence analysis |
| `sources` | Array[Source] | List of sources used for verification (max 10) |
| `tools_used` | Array[string] | Always includes both tools: ["web_search", "news_search"] |

### Source Object

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Title of the source article/page |
| `url` | string | URL to the source |
| `type` | string | Either "web" or "news" |

## 🧪 Testing

### Running the Test Suite

```bash
python test.py
```

This runs comprehensive tests including:
- ✅ API key validation
- ✅ Web search tool verification
- ✅ News search tool verification
- ✅ LangChain tool integration
- ✅ All 4 mandatory test claims
- ✅ Hard rule verification (both tools called)

### Manual Test Claims

Test the following claims via the API:

#### Test 1: False Claim
```bash
curl -X POST "http://localhost:8000/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"claim": "The Earth is flat."}'
```
**Expected:** Likely False with scientific evidence

#### Test 2: True Claim
```bash
curl -X POST "http://localhost:8000/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"claim": "OpenAI released GPT-4 in 2023."}'
```
**Expected:** Likely True with official announcements

#### Test 3: Dangerous Misinformation
```bash
curl -X POST "http://localhost:8000/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"claim": "Drinking bleach can cure COVID-19."}'
```
**Expected:** Likely False with health authority warnings

#### Test 4: Recent False Claim
```bash
curl -X POST "http://localhost:8000/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"claim": "Google is shutting down Gmail in 2025."}'
```
**Expected:** Likely False with no credible sources

## 🔧 Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | FastAPI | REST API and automatic documentation |
| **AI Agent** | LangChain | Tool orchestration and reasoning |
| **LLM** | Google Gemini 2.0 Flash | Evidence analysis and verdict generation |
| **Web Search** | Google Serper API | General web evidence retrieval |
| **News Search** | NewsAPI | Recent news article retrieval |
| **Data Validation** | Pydantic | Request/response schema validation |
| **Environment** | python-dotenv | Secure API key management |

## 🤖 How the Agent Works

### 1. ReAct Agent Pattern

The agent uses the **Reasoning + Acting (ReAct)** pattern:

```
Thought → Action → Observation → Thought → Final Answer
```

### 2. Tool Calling Flow

```
1. User submits claim to API
   ↓
2. FastAPI route calls agent.py run_fact_check_agent()
   ↓
3. LangChain agent initializes with both tools:
   - web_search (Google Serper)
   - news_search (NewsAPI)
   ↓
4. Agent decides which tools to invoke:
   - web_search(claim) → Get general web evidence
   - news_search(claim) → Get recent news evidence
   ↓
5. Results aggregated from both sources
   ↓
6. Gemini LLM analyzes combined evidence
   ↓
7. Agent produces structured verdict with:
   - Classification (True/False/Uncertain)
   - Explanation (evidence-based reasoning)
   - Source citations (title, URL, type)
```

### 3. Fact-Checking Logic

**Evidence Analysis:**
- Searches multiple sources for supporting evidence
- Identifies contradicting evidence
- Evaluates source credibility (news sources vs web results)
- Weighs evidence quantity and consistency
- Determines confidence level based on evidence strength

**Verdict Generation:**
- **Likely True**: Strong supporting evidence from multiple sources, minimal contradictions
- **Likely False**: Strong contradicting evidence from credible sources
- **Uncertain**: Mixed evidence, conflicting information, or insufficient data

### 4. Tool Integration

Both tools are mandatory and always called:

**Web Search Tool** (Google Serper API)
- Searches general web content
- Returns latest web pages and articles
- Provides broad evidence coverage

**News Search Tool** (NewsAPI)
- Searches recent news articles
- Returns authoritative news sources
- Prioritizes current and breaking information

## 📦 Dependencies

```
fastapi==0.104.1              # Web framework
uvicorn==0.24.0               # ASGI server
langchain==0.1.0              # LLM orchestration
langchain-core==0.1.0         # Core LangChain components
langchain-google-genai==0.0.13 # Gemini integration
google-generativeai==0.3.0    # Google Gemini API
python-dotenv==1.0.0          # Environment management
requests==2.31.0              # HTTP client
pydantic==2.5.0               # Data validation
```

Install all dependencies with:
```bash
pip install -r requirements.txt
```

## 🔐 Security & Best Practices

### API Key Management

✅ **Never hardcode API keys** - Always use `.env` file
✅ **Add `.env` to `.gitignore`** - Prevent accidental commits
✅ **Rotate keys regularly** - Update in API provider dashboards
✅ **Use environment variables** - Load from `.env` at runtime

Example `.env`:
```
GOOGLE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
SERPAPI_API_KEY=xxxxxxxxxxxxxxxxxxxx
NEWSAPI_API_KEY=xxxxxxxxxxxxxxxxxxxx
```

### Input Validation

- Pydantic validates all request bodies
- Claim length limited to 1000 characters
- Invalid requests return 422 Unprocessable Entity

### Rate Limiting

Consider adding rate limiting in production:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/fact-check")
@limiter.limit("30/minute")
async def fact_check(request: FactCheckRequest):
    ...
```

## 📊 Performance & Limits

| Metric | Value |
|--------|-------|
| **Average Response Time** | 5-15 seconds |
| **Web Search Results** | 5 results per query |
| **News Search Results** | 5 results per query |
| **Total Sources** | Up to 10 sources |
| **Claim Length** | Max 1000 characters |
| **LLM Model** | Gemini 2.0 Flash |
| **LLM Temperature** | 0.2 (deterministic) |

### Performance Tips

1. **Cache repeated claims** - Store results for identical claims
2. **Batch requests** - Process multiple claims in sequence
3. **Monitor API quotas** - Check remaining API calls
4. **Use async endpoints** - Non-blocking request handling

## 🐛 Troubleshooting

### Issue: `GOOGLE_API_KEY not found`

**Solution:** Ensure `.env` file exists with correct variable
```bash
# Create .env file
echo "GOOGLE_API_KEY=your_key" > .env
echo "SERPAPI_API_KEY=your_key" >> .env
echo "NEWSAPI_API_KEY=your_key" >> .env
```

### Issue: `Connection timeout to Serper API`

**Solution:** Check internet connection and API status
```bash
# Test Serper API directly
curl -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: your_key" \
  -H "Content-Type: application/json" \
  -d '{"q": "test"}'
```

### Issue: `Tools not called by agent`

**Solution:** Verify agent.py has both @tool decorated functions
```bash
grep -n "@tool" app/agent.py
# Should show: web_search and news_search functions
```

### Issue: `Port 8000 already in use`

**Solution:** Use a different port
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### Issue: `Invalid JSON response`

**Solution:** Check response format with test.py
```bash
python test.py
```

### Issue: `Gemini API quota exceeded`

**Solution:** Wait for quota reset or upgrade to paid tier
- Free tier: Limited requests per day
- Paid tier: Higher quotas available

## 📈 Development Roadmap

- [ ] Add response caching with Redis
- [ ] Implement multi-language support
- [ ] Add source credibility scoring system
- [ ] Create admin dashboard for statistics
- [ ] Add fact-checking history per user
- [ ] Implement cost tracking per API
- [ ] Add webhook notifications for results
- [ ] Develop mobile app integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Commit changes with clear messages
   ```bash
   git commit -m "Add amazing feature"
   ```
4. Push to your branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👤 Author

**Rahageer90**
- GitHub: [@Rahageer90](https://github.com/Rahageer90)
- Repository: [fact_check_agent](https://github.com/Rahageer90/fact_check_agent)

## 📞 Support & Issues

For bugs, questions, or suggestions:

1. **Check existing issues** - Search GitHub issues first
2. **Create a new issue** - Provide claim, error message, and logs
3. **Include logs** - Attach test.py output
4. **Specify environment** - Python version, OS, API status

## 🙏 Acknowledgments

- [LangChain](https://python.langchain.com/) - Agent framework and tool orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) - Powerful LLM for reasoning
- [Google Serper](https://serper.dev/) - Web search API
- [NewsAPI](https://newsapi.org/) - News aggregation API

## 📚 Additional Resources

- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/)
- [FastAPI User Guide](https://fastapi.tiangolo.com/learn/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Google Gemini API](https://ai.google.dev/)

---

**Last Updated:** January 26, 2026
**Version:** 1.0.0
**Status:** Production Ready ✅
