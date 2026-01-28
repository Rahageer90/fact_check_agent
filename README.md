# Fact-Check AI Agent

A sophisticated AI-powered fact-checking system that verifies claims by querying web sources and news articles. Built with FastAPI, LangChain, and Model Context Protocol (MCP) for robust and scalable fact verification.

## Features

- **Automated Fact-Checking**: Uses AI agents to analyze claims and determine veracity
- **Multi-Source Verification**: Queries both general web results and recent news articles
- **RESTful API**: Clean FastAPI endpoints for easy integration
- **MCP Tool Integration**: Leverages Model Context Protocol for extensible tool management
- **Structured Responses**: Returns verdicts, explanations, sources, and tool usage tracking
- **Async Processing**: High-performance asynchronous operations for scalability

## Architecture

For detailed system architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Prerequisites

- Python 3.8+
- API Keys for:
  - [Google Serper API](https://serper.dev/) (for web search)
  - [NewsAPI](https://newsapi.org/) (for news search)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fact_check_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Setup

1. Create a `.env` file in the root directory:
```env
SERPAPI_API_KEY=your_serper_api_key_here
NEWSAPI_API_KEY=your_newsapi_api_key_here
```

2. Obtain API keys:
   - **Serper API**: Sign up at [serper.dev](https://serper.dev/) and get your API key
   - **NewsAPI**: Sign up at [newsapi.org](https://newsapi.org/) and get your API key

## Running the Application

The application consists of two servers that must run simultaneously:

### 1. Start the MCP Server (Tools Provider)
```bash
fastmcp run mcp_tools/mcp_server.py --transport sse
```
This starts the MCP server on `http://localhost:8000/sse`

### 2. Start the FastAPI Application
```bash
python -m uvicorn app.main:app --port 9090
```
This starts the main API server on `http://localhost:9090`

## API Usage

### Fact-Check Endpoint

**POST** `/fact-check`

Verify a claim by sending a JSON request with the claim text.

#### Request
```json
{
  "claim": "The Earth is flat"
}
```

#### Response
```json
{
  "verdict": "Likely False",
  "explanation": "Based on extensive scientific evidence from multiple sources...",
  "sources": [
    {
      "title": "NASA Earth Facts",
      "url": "https://www.nasa.gov/earth-facts",
      "type": "web"
    }
  ],
  "tools_used": ["web_search", "news_search"]
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:9090/fact-check" \
     -H "Content-Type: application/json" \
     -d '{"claim": "Climate change is caused by human activity"}'
```

### Health Check

**GET** `/`

Returns a simple status message.

```bash
curl http://localhost:9090/
```

## API Documentation

Once both servers are running, visit `http://localhost:9090/docs` for interactive Swagger UI documentation.

## Development

### Project Structure
```
fact_check_agent/
├── app/
│   ├── agent.py          # Core fact-checking agent logic
│   ├── main.py           # FastAPI application
│   └── schemas.py        # Pydantic data models
├── mcp_tools/
│   ├── __init__.py
│   └── mcp_server.py    # MCP tool implementations
├── services/
│   └── gemini.py         # LLM integration
├── requirements.txt      # Python dependencies
├── TODO.md              # Development roadmap
├── ARCHITECTURE.md      # System architecture
└── README.md            # This file
```

### Testing

1. Ensure both servers are running
2. Use the `/docs` endpoint to test the API interactively
3. Or use cURL commands to test specific claims

### Adding New Tools

To extend the system with additional fact-checking tools:

1. Add tool functions in `mcp_tools/mcp_server.py`
2. Decorate with `@mcp.tool()`
3. Update the agent logic in `app/agent.py` if needed

## Troubleshooting

### Common Issues

1. **"No tools found on MCP server"**
   - Ensure the MCP server is running on port 8000
   - Check that API keys are properly set in `.env`

2. **API Key Errors**
   - Verify `.env` file exists and contains correct keys
   - Ensure no extra spaces or quotes around key values

3. **Connection Refused**
   - Confirm both servers are started in the correct order
   - Check port availability (9090 for API, 8000 for MCP)

### Logs

Check console output for detailed error messages and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]

## Disclaimer

This tool provides automated fact-checking assistance but should not be considered infallible. Always verify critical information through multiple trusted sources.
