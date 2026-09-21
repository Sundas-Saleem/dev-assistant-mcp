# Dev Assistant MCP Server

A multi-tool [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server built with [FastMCP](https://github.com/jlowin/fastmcp) that gives AI assistants three powerful engineering tools.

## Tools

| Tool | What it does |
|---|---|
| `analyze_logs` | Parses raw log output, extracts errors & stack traces, returns a structured diagnosis |
| `review_code` | Reviews a code snippet for issues, anti-patterns, and improvements |
| `fetch_github_issues` | Fetches and summarizes open issues from any public GitHub repository |

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/sundas-saleem/dev-assistant-mcp.git
cd dev-assistant-mcp
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
python server.py
```

### 4. Connect to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dev-assistant": {
      "command": "python",
      "args": ["/path/to/dev-assistant-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop — you'll see the three tools available in any conversation.

## Usage Examples

### Analyze logs
> "Here are my production logs from last night, can you tell me what went wrong?"

### Review code
> "Review this Python function for issues before I merge it."

### GitHub issues
> "Summarize the open bugs in psf/requests"

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Project Structure

```
dev-assistant-mcp/
├── server.py           # MCP server entry point
├── requirements.txt
├── tools/
│   ├── log_analyzer.py    # Log parsing & error extraction
│   ├── code_reviewer.py   # Static code analysis
│   └── github_issues.py   # GitHub API integration
└── tests/
    └── test_tools.py      # pytest test suite
```

## Built With

- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP server framework
- Python standard library only (no heavy dependencies)

## Author

**Sundas Saleem** — Senior Software Engineer  
[github.com/sundas-saleem](https://github.com/sundas-saleem) · [sundas-saleem.github.io](https://sundas-saleem.github.io)
