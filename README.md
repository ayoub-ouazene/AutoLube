# Oil E-Commerce AI Assistant

This project is an in-progress Python backend/agent for an oil recommendation assistant. The current runnable version starts a terminal chat session and uses a main LangChain/Groq agent plus a search sub-agent for vehicle oil, gearbox oil, and oil filter recommendations.

## Project Structure

```text
.
├── agent/
│   ├── main_agent.py              # Current CLI entry point
│   ├── prompts.py                 # Main and search agent prompts
│   ├        # Older nested dependency file
│   └── search_agent/
│       ├── agent.py               # Search sub-agent tool wrapper
│       └── tools.py               # DDGS, Tavily, scraping, and extraction tools
├── Reports/                       # Existing report documents
├── schema.py                      # Pydantic tool input schema
├── requirements.txt               # Install dependencies from here
└── README.md
```

## Requirements

- Python 3.10 or newer is recommended.
- A Groq API key.
- A Tavily API key for Tavily fallback search.

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you are using Command Prompt instead of PowerShell, activate the environment with:

```cmd
.venv\Scripts\activate.bat
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Variables

Create a file named `.env` inside the `agent` folder:

```text
agent/.env
```

Add the following values:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_KEY2=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

`GROQ_API_KEY2` is used by the main agent in `agent/main_agent.py`. `GROQ_API_KEY` is used by the search agent and extraction model. You can use the same Groq key for both values unless you intentionally want separate keys.

## Run The Current Version

Run the project from the root folder:

```powershell
python -m agent.main_agent
```

The assistant starts an interactive terminal session. Type your customer request when prompted, and type `exit` or `quit` to stop.

Example:

```text
Customer: I need engine oil for a 2018 Renault Clio 1.5 dCi with 180000 km
```

## Notes For Development

- The project currently runs as a CLI application.
- Backend/API functions are still being implemented.
- Install dependencies from the root `requirements.txt`; it includes packages imported by the current code.
- Search uses DDGS first and Tavily as a fallback/verification source.
- Some searches depend on external websites, so results may vary depending on network access and source availability.
