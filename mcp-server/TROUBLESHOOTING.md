# MCP Server Troubleshooting Guide

## Common Issues and Solutions

### 1. Semantic Scholar Rate Limit (429 Error)

**Error Message:**
```
Error fetching from Semantic Scholar: 429 Client Error: Too Many Requests
```

**Cause:**
Semantic Scholar API has rate limits:
- **Unauthenticated**: ~100 requests per 5 minutes
- **With API Key**: Higher limits (requires registration)

**Solutions:**

#### Immediate Fix: Wait and Retry
Simply wait 5 minutes before trying again. The rate limit resets every 5 minutes.

#### Solution 1: Use Smaller Batches
Instead of:
```
"Fetch 100 papers about transformers"
```

Try:
```
"Fetch 10 papers about transformers"
```

The tool now includes a 1-second delay between requests to help prevent rate limiting.

#### Solution 2: Get a Semantic Scholar API Key (Recommended)

1. **Register for API Key** (free):
   - Visit: https://www.semanticscholar.org/product/api
   - Sign up for an account
   - Request an API key

2. **Add API Key to Environment**:
   ```bash
   export SEMANTIC_SCHOLAR_API_KEY="your-api-key-here"
   ```

3. **Update SemanticScholarFetcher** to use the key:
   Edit `mindscout/fetchers/semanticscholar.py` and add the key to headers:
   ```python
   import os

   self.session.headers.update({
       "User-Agent": "MindScout/0.2",
       "x-api-key": os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
   })
   ```

#### Solution 3: Use arXiv Instead
For broad topic exploration, use arXiv which has no rate limits:
```
"Fetch the latest AI papers from arXiv"
```

---

### 2. MCP Server Not Appearing in Claude Desktop

**Symptoms:**
- No 🔌 icon
- Claude doesn't see Mind Scout tools

**Solutions:**

#### Check 1: Verify Config File
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Should look like:
```json
{
  "mcpServers": {
    "mindscout": {
      "command": "/Users/kate/.pyenv/shims/python",
      "args": ["/Users/kate/projects/agento/mcp-server/server.py"]
    }
  }
}
```

#### Check 2: Verify Python Path
```bash
which python
```

Make sure it matches the `command` in your config.

#### Check 3: Test Server Manually
```bash
python /Users/kate/projects/agento/mcp-server/server.py
```

Should run without errors.

#### Check 4: Check Logs
```bash
tail -50 ~/Library/Logs/Claude/mcp-server-mindscout.log
```

Look for "Server started and connected successfully"

#### Check 5: Completely Restart Claude Desktop
1. Quit Claude Desktop (Cmd+Q)
2. Wait 5 seconds
3. Reopen Claude Desktop

---

### 3. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'mindscout'
```

**Solution:**
Install Mind Scout in development mode:
```bash
cd /Users/kate/projects/agento
pip install -e .
```

---

### 4. Database Errors

**Error:**
```
sqlite3.OperationalError: unable to open database file
```

**Solutions:**

#### Check Database Exists
```bash
ls -la ~/.mindscout/mindscout.db
```

#### Initialize if Missing
```bash
mindscout profile list
```

This will create the database if it doesn't exist.

#### Check Permissions
```bash
chmod 644 ~/.mindscout/mindscout.db
```

---

### 5. Fetch Returns No Results

**Issue:** Tool runs but returns 0 new articles

**Possible Causes:**

#### Cause 1: Articles Already Exist
The tool filters duplicates automatically. Check:
```bash
mindscout list --limit 10
```

#### Cause 2: Query Too Specific
Try broader queries:
- Instead of: "attention mechanisms in vision transformers for image classification"
- Try: "vision transformers"

#### Cause 3: Filters Too Restrictive
Remove strict filters:
- Lower `min_citations` requirement
- Expand `year` range

---

### 6. Vector Store / Semantic Search Errors

**Error:**
```
Vector store not initialized
```

**Solution:**
Index your articles:
```bash
mindscout index
```

This creates embeddings for semantic search.

---

## Debug Mode

### Enable Verbose Logging

Create a debug version of the server:

```bash
cat > /tmp/mcp_debug.py << 'EOF'
import sys
import logging
sys.path.insert(0, "/Users/kate/projects/agento")

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from mcp_server.server import mcp
mcp.run()
EOF

python /tmp/mcp_debug.py
```

### Test Individual Tools

Create a test script:

```python
import sys
sys.path.insert(0, "/Users/kate/projects/agento")

from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

fetcher = SemanticScholarFetcher()
try:
    papers = fetcher.fetch(query="test", limit=2)
    print(f"Success! Got {len(papers)} papers")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    fetcher.close()
```

---

## Rate Limit Best Practices

### For Semantic Scholar:

1. **Use Smaller Limits**: Start with `limit=10-20` instead of 100
2. **Add Delays**: Wait 5-10 seconds between consecutive requests
3. **Use Specific Queries**: More specific = fewer results = less API usage
4. **Get an API Key**: Free registration at semanticscholar.org
5. **Cache Results**: The tool automatically prevents duplicates

### For arXiv:

- No rate limits!
- Fetch freely from RSS feeds
- Best for category-based browsing

---

## Getting Help

### Check Logs First
```bash
# MCP server logs
tail -100 ~/Library/Logs/Claude/mcp-server-mindscout.log

# Look for errors
grep -i error ~/Library/Logs/Claude/mcp-server-mindscout.log
```

### Test CLI Commands
Before using MCP, test with CLI:
```bash
# Test arXiv
mindscout fetch -c cs.AI

# Test Semantic Scholar
mindscout search --source semanticscholar --query "test" -n 5
```

### Verify Setup
```bash
# Check Python
python --version  # Should be 3.10+

# Check MCP SDK
pip show mcp

# Check Mind Scout
pip show mindscout
```

---

## Quick Diagnostic

Run this to check everything:

```bash
echo "=== Mind Scout MCP Diagnostics ==="
echo ""
echo "1. Python Version:"
python --version
echo ""
echo "2. MCP SDK:"
pip show mcp | grep Version
echo ""
echo "3. Database:"
ls -lh ~/.mindscout/mindscout.db 2>&1
echo ""
echo "4. Server Test:"
timeout 5 python /Users/kate/projects/agento/mcp-server/server.py 2>&1 || echo "Server loads OK"
echo ""
echo "5. Recent MCP Logs:"
tail -5 ~/Library/Logs/Claude/mcp-server-mindscout.log 2>&1 || echo "No logs yet"
```
