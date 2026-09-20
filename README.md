# TripMate AI

TripMate AI is a multi-agent travel planner that turns a natural-language request into a practical trip draft. It brings together flight research, hotel discovery, weather, budget guidance, and a day-by-day itinerary in one reviewable experience.

The app is built with FastAPI, LangGraph, Groq, PostgreSQL, and Model Context Protocol (MCP) tools.

## What it does

- Routes each request through only the travel specialists it needs.
- Researches flights with AviationStack, hotels with Tavily, and weather with a local OpenWeather MCP server.
- Creates budget-aware itineraries and clearly labels estimates when live prices are unavailable.
- Pauses for human review before producing a final polished plan.
- Persists a planning thread in PostgreSQL so approval and revision requests can resume the same workflow.
- Provides a responsive, animated web UI with loading progress, selectable trip prompts, and reduced-motion support.

## How it works

```text
Traveler request
      |
Input guardrail
      |
Supervisor -> flight / hotel / weather / budget specialists
      |
Draft itinerary
      |
Human approval or revision feedback
      |
Final travel plan
```

The supervisor always includes the itinerary agent and dynamically adds the other specialists based on the request. A blocked, non-travel request ends before any research is performed.

## MCP integrations

| Capability | Integration | Transport |
| --- | --- | --- |
| Hotel research | Tavily | Remote streamable HTTP MCP |
| Flight data | AviationStack | Local `uvx aviationstack-mcp` stdio MCP |
| Current weather and forecast | OpenWeather | Local Python stdio MCP server |

If an external service is unavailable, the relevant specialist returns a clear fallback rather than failing the whole plan.

## Prerequisites

- Python 3.10+
- PostgreSQL 15+ for local development, or Docker Desktop for the containerized setup
- API keys for Groq, Tavily, AviationStack, and OpenWeather
- `uvx` available on your PATH when running outside Docker (used by the AviationStack MCP server)

## Quick start with Docker

Docker Compose starts both the app and PostgreSQL.

```bash
cp .env.example .env
# Add your API keys to .env
docker compose up --build
```

Open <http://localhost:8000>.

To run in the background, use `docker compose up -d --build`. See [DOCKER.md](DOCKER.md) for deployment, troubleshooting, and operations guidance.

## Local setup

1. Create the environment file.

   ```bash
   cp .env.example .env
   ```

   In PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Create and activate a virtual environment, then install dependencies.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   In PowerShell:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Start PostgreSQL and set `DATABASE_URL` in `.env`, then launch the app.

   ```bash
   python app.py
   ```

4. Open <http://127.0.0.1:8001>.

## Configuration

Copy `.env.example` and set the following values:

```env
DATABASE_URL=postgresql://tripmate_user:change-me@localhost:5432/travel_db
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
DEFAULT_ORIGIN_IATA=DEL
```

`DEFAULT_ORIGIN_IATA` is used when a traveler does not provide a departure airport. Keep `.env` private; it is intentionally excluded from Git.

## API

### Health check

```bash
curl http://127.0.0.1:8001/health
```

### Start a travel plan

```bash
curl -X POST http://127.0.0.1:8001/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 3-day trip to Tokyo from Delhi with a budget of $1200"}'
```

When the draft is ready, the response includes `thread_id`, `requires_approval`, and the itinerary. Use that thread ID to finalize or revise it.

### Approve or revise a draft

```bash
curl -X POST http://127.0.0.1:8001/api/travel/approve \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"user_your_thread_id","approved":false,"feedback":"Use a hotel near public transit."}'
```

Set `approved` to `true` to finalize the draft. Set it to `false` and provide feedback to request a revised final response.

## Project structure

```text
TripPlan_Ai/
├── app.py                       # FastAPI routes and lifecycle management
├── backend.py                   # LangGraph workflow and persistence
├── mcp_client.py                # MCP clients for hotel, flight, and weather tools
├── custom_weather_mcp_server.py # Local OpenWeather MCP server
├── templates/index.html         # Web application markup
├── static/style.css             # Responsive visual design and animations
├── static/script.js             # UI behavior, loading state, and review flow
├── docker-compose.yml           # App + PostgreSQL local stack
├── Dockerfile                   # Container image definition
├── .env.example                 # Configuration template
└── requirements.txt             # Python dependencies
```

## Notes for production

- Use a strong database password and a managed PostgreSQL instance where appropriate.
- Configure secrets through your platform's secret manager; do not bake them into images or source code.
- Serve the application behind HTTPS and restrict any public database port.
- Live data sources can have coverage, rate-limit, or pricing limitations. Present flight fares and availability as guidance until confirmed with a provider.

## Contributing

1. Create a branch for your change.
2. Keep credentials and generated files out of commits.
3. Run the relevant checks and verify the web flow locally.
4. Open a pull request with a concise description of the change.

## License

Add a license file before distributing this project publicly.
