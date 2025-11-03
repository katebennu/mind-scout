# Mind Scout MCP Server

Model Context Protocol (MCP) server for Mind Scout, enabling AI assistants like Claude Desktop to directly access your research library.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that allows AI assistants to securely access external tools and data sources. By installing this MCP server, you enable AI assistants to:

- Search your research paper library
- Get personalized recommendations
- View and rate articles
- Manage your profile and interests

## Tools Available

The Mind Scout MCP server exposes 9 tools:

### 1. `search_papers`
Search research papers using semantic search with natural language queries.

**Parameters:**
- `query` (string): Natural language search query
- `limit` (int, optional): Maximum results (default: 10)

**Example:** "Search for papers about attention mechanisms in transformers"

### 2. `get_recommendations`
Get personalized paper recommendations based on your interests and reading history.

**Parameters:**
- `limit` (int, optional): Maximum recommendations (default: 10)

**Example:** "Get 5 paper recommendations for me"

### 3. `get_article`
Retrieve detailed information about a specific article by ID.

**Parameters:**
- `article_id` (int): The unique ID of the article

**Example:** "Show me details for article 42"

### 4. `list_articles`
Browse articles in the library with filtering and pagination.

**Parameters:**
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Articles per page (default: 10)
- `unread_only` (bool, optional): Show only unread articles (default: false)
- `source` (string, optional): Filter by source (e.g., "arxiv")
- `sort_by` (string, optional): Sort order - "recent", "rating", or "citations" (default: "recent")

**Example:** "List unread papers from arxiv"

### 5. `rate_article`
Rate a research paper from 1 to 5 stars.

**Parameters:**
- `article_id` (int): The unique ID of the article
- `rating` (int): Rating from 1 (poor) to 5 (excellent)

**Example:** "Rate article 42 as 5 stars"

### 6. `mark_article_read`
Mark a paper as read or unread.

**Parameters:**
- `article_id` (int): The unique ID of the article
- `is_read` (bool, optional): True to mark as read (default: true)

**Example:** "Mark article 42 as read"

### 7. `get_profile`
View user profile, interests, and comprehensive reading statistics.

**Parameters:** None

**Example:** "Show my profile and statistics"

### 8. `update_interests`
Update your research interests to improve recommendations.

**Parameters:**
- `interests` (list of strings): Research topics

**Example:** "Update my interests to transformers, computer vision, and RL"

### 9. `fetch_articles` (New!)
Fetch new research papers from arXiv or Semantic Scholar and add them to your library.

**Parameters:**
- `source` (string): Where to fetch from - "arxiv" or "semanticscholar"
- `query` (string, optional): Search query (required for Semantic Scholar)
- `categories` (list of strings, optional): arXiv categories (default: ["cs.AI", "cs.LG", "cs.CV", "cs.CL"])
- `limit` (int, optional): Maximum papers to fetch (default: 20)
- `min_citations` (int, optional): Minimum citation count filter (Semantic Scholar only)
- `year` (string, optional): Year filter like "2024" or "2023-2024" (Semantic Scholar only)

**Examples:**
- "Fetch the latest AI papers from arXiv"
- "Fetch papers about diffusion models from Semantic Scholar"
- "Get highly cited papers about transformers from 2024"
- "Fetch computer vision papers with at least 100 citations"

## Installation

### Prerequisites

- Python 3.10 or higher
- Mind Scout installed and configured
- MCP SDK: `pip install "mcp[cli]>=1.2.0"`

### Install in Claude Desktop

1. **Install the MCP SDK** (if not already installed):
   ```bash
   pip install "mcp[cli]>=1.2.0"
   ```

2. **Add to Claude Desktop configuration**:

   On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "mindscout": {
         "command": "python",
         "args": [
           "/Users/kate/projects/agento/mcp-server/server.py"
         ]
       }
     }
   }
   ```

   **Note:** Replace `/Users/kate/projects/agento` with your actual project path.

3. **Restart Claude Desktop**

4. **Verify installation**: Look for the 🔌 icon in Claude Desktop indicating MCP servers are connected.

## Usage Examples

Once installed, you can use natural language commands in Claude Desktop:

### Search & Browse
```
User: "Search my Mind Scout library for papers about transformers"
Claude: [Uses search_papers tool to search the library]

User: "Show me unread papers from arxiv"
Claude: [Uses list_articles tool with filters]
```

### Fetch New Papers
```
User: "Fetch the latest AI papers from arXiv"
Claude: [Uses fetch_articles tool with source="arxiv"]

User: "Find highly cited papers about diffusion models from 2024"
Claude: [Uses fetch_articles with source="semanticscholar", query, year, min_citations]

User: "Get new transformer papers from Semantic Scholar"
Claude: [Uses fetch_articles to search and add to library]
```

### Recommendations & Ratings
```
User: "What are my top 3 unread recommendations?"
Claude: [Uses get_recommendations tool with limit=3]

User: "Rate that first paper 5 stars"
Claude: [Uses rate_article tool]
```

### Profile & Stats
```
User: "Show my reading statistics"
Claude: [Uses get_profile tool]

User: "Update my interests to include computer vision and RL"
Claude: [Uses update_interests tool]
```

## Development

### Test the server

Use the MCP Inspector to test the server locally:

```bash
cd mcp-server
mcp dev server.py
```

This opens an interactive inspector where you can test each tool.

### Project Structure

```
mcp-server/
├── server.py           # Main MCP server implementation
├── pyproject.toml      # Python package configuration
└── README.md           # This file
```

### Adding New Tools

To add a new tool, add a function with the `@mcp.tool()` decorator:

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int = 10) -> dict:
    """Tool description that Claude will see.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 10)

    Returns:
        Result description
    """
    # Implementation
    return {"result": "data"}
```

## Troubleshooting

**Server not showing in Claude Desktop:**
- Check the configuration file path is correct
- Ensure Python path is correct (`which python`)
- Restart Claude Desktop completely
- Check logs: `~/Library/Logs/Claude/` on macOS

**Import errors:**
- Ensure Mind Scout is installed: `pip install -e .` from project root
- Check Python version: `python --version` (must be 3.10+)

**Database errors:**
- Ensure Mind Scout database exists and is initialized
- Run `mindscout profile list` to verify setup

## Security

The MCP server runs locally on your machine and only has access to your Mind Scout database. No data is sent to external services. The server communicates with Claude Desktop via stdio (standard input/output).

## License

Same as Mind Scout main project.
