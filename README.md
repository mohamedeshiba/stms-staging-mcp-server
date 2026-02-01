# Creating an MCP Server with FastMCP

A comprehensive guide to building Model Context Protocol (MCP) servers using Python and FastMCP.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installing uv](#installing-uv)
- [Project Setup](#project-setup)
- [Installing Dependencies](#installing-dependencies)
- [Creating Your First MCP Server](#creating-your-first-mcp-server)
- [Running the Server](#running-the-server)
- [Adding to Cursor](#adding-to-cursor)
- [Verifying the Server](#verifying-the-server)
- [Advanced Features](#advanced-features)

---

## Prerequisites
- Python 3.10+ (uv will manage this for you)
- Terminal/Command Line access

---

## Installing uv

[uv](https://docs.astral.sh/uv/) is a fast Python package and project manager that simplifies dependency management.

### macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Project Setup

### 1. Create a New Project Directory

```bash
mkdir my-mcp-server
cd my-mcp-server
```

### 2. Initialize the Project with uv

```bash
uv init
```

This creates:
- `pyproject.toml` - Project configuration and dependencies
- `.python-version` - Python version specification
- `hello.py` - Sample Python file (you can delete or rename this)
- `.gitignore` - Git ignore rules


## Installing Dependencies

### Add the MCP Package

```bash
uv add "mcp[cli]"
```

This installs the MCP library with CLI tools. Your `pyproject.toml` will look like:

```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
description = "My MCP Server"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "mcp[cli]>=1.26.0",
]
```

### Sync Dependencies

```bash
uv sync
```

This creates a virtual environment and installs all dependencies.

---

## Creating Your First MCP Server

Create a file called `server.py`:

```python
from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
mcp = FastMCP("MyServer")


# Define a tool - functions that can be called by the AI
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@mcp.tool()
def greet(name: str) -> str:
    """Generate a greeting for the given name."""
    return f"Hello, {name}! Welcome to MCP."


# Define a resource - data that can be read by the AI
@mcp.resource("info://server")
def get_server_info() -> str:
    """Get information about this server."""
    return "This is my first MCP server!"


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"


# Define a prompt - reusable prompt templates
@mcp.prompt()
def code_review(code: str, language: str = "python") -> str:
    """Generate a code review prompt."""
    return f"""Please review the following {language} code and provide feedback:

```{language}
{code}
```

Focus on:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Suggestions for improvement
"""


# Run with stdio transport (required for Cursor integration)
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Running the Server

### Test Locally

```bash
uv run server.py
```

The server will start and wait for input via stdio. Press `Ctrl+C` to stop.

### Test with a Sample Request

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run server.py
```

You should see a JSON response listing your tools.

---

## Adding to Cursor

### 1. Locate the Cursor MCP Configuration

The configuration file is at:
- **macOS/Linux**: `~/.cursor/mcp.json`

### 2. Add Your Server

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "uv",
      "type": "stdio",
      "args": [
        "run",
        "server.py"
      ],
      "cwd": "/absolute/path/to/my-mcp-server",
      "env": {}
    }
  }
}
```

**Important**: Replace `/absolute/path/to/my-mcp-server` with the actual path to your project.

### 3. Reload Cursor

Press `Cmd+Shift+P` (macOS)
```
Developer: Reload Window
```

---

## Verifying the Server

### Check Server Status in Cursor

1. Open **Cursor Settings** (Cmd+, or Ctrl+,)
2. Search for "MCP"
3. Look for your server - a green indicator means it's running

### Check via MCP Files

Cursor creates status files for each MCP server:

```
~/.cursor/projects/<workspace>/mcps/user-<server-name>/
├── SERVER_METADATA.json    # Server info
├── tools/                  # Registered tools
│   └── add.json
│   └── multiply.json
│   └── greet.json
├── resources/              # Registered resources (if any)
└── prompts/                # Registered prompts (if any)
    └── code_review.json
```

If a `STATUS.md` file exists, the server has errors.

### Test the Tools

Ask the AI in Cursor to use your tools:
- "Use my-mcp-server to add 5 and 3"
- "Use my-mcp-server to greet John"

---

## Advanced Features

### Adding Environment Variables

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "uv",
      "type": "stdio",
      "args": ["run", "server.py"],
      "cwd": "/path/to/my-mcp-server",
      "env": {
        "API_KEY": "your-api-key",
        "DEBUG": "true"
      }
    }
  }
}
```

Access in Python:
```python
import os
api_key = os.environ.get("API_KEY")
```

### Async Tools

```python
import httpx

@mcp.tool()
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### Tools with Complex Types

```python
from typing import List, Dict

@mcp.tool()
def process_items(items: List[str]) -> Dict[str, int]:
    """Count occurrences of each item."""
    result = {}
    for item in items:
        result[item] = result.get(item, 0) + 1
    return result
```

### Error Handling

```python
@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### Context and Dependencies

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("MyServer")

@mcp.tool()
async def get_request_info(ctx: Context) -> str:
    """Get information about the current request."""
    return f"Request ID: {ctx.request_id}"
```

---

## Project Structure

A typical MCP server project:

```
my-mcp-server/
├── .gitignore
├── .python-version
├── .venv/                  # Virtual environment (created by uv)
├── pyproject.toml          # Project config and dependencies
├── uv.lock                 # Lock file for reproducible builds
├── server.py               # Main MCP server
└── README.md
```

---

## Troubleshooting

### Server Not Starting

1. Check the path in `mcp.json` is correct
2. Ensure `uv` is in your PATH
3. Run `uv sync` in the project directory
4. Test manually: `cd /path/to/project && uv run server.py`

### Tools Not Appearing

1. Reload Cursor after adding the server
2. Check for syntax errors in your Python code
3. Verify the server uses `transport="stdio"`

### Permission Errors

Ensure Cursor has access to the project directory and `uv` binary.

### Check Logs

Run the server manually to see error output:
```bash
cd /path/to/my-mcp-server
uv run server.py 2>&1
```

---

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Cursor MCP Guide](https://docs.cursor.com/context/model-context-protocol)
