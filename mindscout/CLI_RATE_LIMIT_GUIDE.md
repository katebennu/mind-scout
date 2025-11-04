# CLI Rate Limit Mitigation Guide

## What Changed

The Semantic Scholar fetcher now includes:
- **Automatic retry with exponential backoff** (3 retries)
- **Helpful error messages** when rate limited
- **Progressive delays**: 2s, 4s, 8s between retries
- **Returns partial results** if rate limited

## How It Works

### Before (Old Behavior)
```bash
$ mindscout search --source semanticscholar --query "transformers" -n 100
Error fetching from Semantic Scholar: 429 Client Error
# Nothing saved, confusing error
```

### After (New Behavior)
```bash
$ mindscout search --source semanticscholar --query "transformers" -n 100
⚠️  Rate limit hit. Waiting 2 seconds before retry 1/3...
⚠️  Rate limit hit. Waiting 4 seconds before retry 2/3...
⚠️  Rate limit hit. Waiting 8 seconds before retry 3/3...
❌ Rate limit exceeded after 3 retries.
   Semantic Scholar allows ~100 requests per 5 minutes.
   Please wait a few minutes and try again, or get an API key at:
   https://www.semanticscholar.org/product/api
# Returns the papers fetched before rate limit
```

## Best Practices

### 1. Use Smaller Batches

Instead of fetching 100 papers at once:
```bash
# ❌ Bad - likely to hit rate limit
mindscout search --source semanticscholar --query "transformers" -n 100

# ✅ Good - fetch in smaller batches
mindscout search --source semanticscholar --query "transformers" -n 20
```

### 2. Add Delays Between Commands

If you need to run multiple searches:
```bash
# Fetch batch 1
mindscout search --source semanticscholar --query "transformers" -n 20

# Wait a bit
sleep 5

# Fetch batch 2
mindscout search --source semanticscholar --query "diffusion models" -n 20
```

### 3. Use Specific Queries

More specific queries = fewer total results = less API usage:
```bash
# ❌ Too broad
mindscout search --source semanticscholar --query "AI" -n 50

# ✅ More specific
mindscout search --source semanticscholar --query "vision transformers for image segmentation" -n 20
```

### 4. Use Filters to Reduce Results

```bash
# Filter by recent and highly cited papers only
mindscout search --source semanticscholar \
  --query "transformers" \
  --year "2024" \
  --min-citations 50 \
  -n 20
```

### 5. Get a Semantic Scholar API Key

**Free API key provides much higher rate limits!**

#### Step 1: Get API Key
1. Visit: https://www.semanticscholar.org/product/api
2. Sign up for an account
3. Request an API key (free)

#### Step 2: Add to Environment
```bash
# Add to your ~/.bashrc or ~/.zshrc
export SEMANTIC_SCHOLAR_API_KEY="your-key-here"

# Or set for current session
export SEMANTIC_SCHOLAR_API_KEY="your-key-here"
```

#### Step 3: Update Fetcher to Use Key
Edit `mindscout/fetchers/semanticscholar.py`:

```python
import os

def __init__(self):
    super().__init__("semanticscholar")
    self.session = requests.Session()

    # Get API key from environment
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    headers = {
        "User-Agent": "MindScout/0.2 (Research Assistant; mailto:user@example.com)"
    }

    # Add API key if available
    if api_key:
        headers["x-api-key"] = api_key
        print("✓ Using Semantic Scholar API key")

    self.session.headers.update(headers)
```

### 6. Use arXiv for Broad Exploration

For general topic exploration, use arXiv (no rate limits):
```bash
# ✅ No rate limits!
mindscout fetch -c cs.AI cs.LG cs.CV

# Fetches latest papers from multiple categories
```

## Rate Limit Reference

### Semantic Scholar Limits

| Account Type | Rate Limit | Per |
|-------------|------------|-----|
| No API Key | ~100 requests | 5 minutes |
| With Free API Key | ~1,000 requests | 5 minutes |
| Academic/Research | Higher limits | Contact S2 |

### Request Counting

Each batch counts as 1 request:
- Fetching 20 papers = 1 request
- Fetching 100 papers = 1 request (if in one call)
- BUT: Pagination counts separately!

Example:
```bash
# This uses 1 request (limit=20, fits in one call)
mindscout search --source semanticscholar --query "test" -n 20

# This uses 2 requests (limit=150, needs pagination: 100 + 50)
mindscout search --source semanticscholar --query "test" -n 150
```

## Testing Rate Limits

### Check Current Rate Limit Status

```bash
# Test with a small query
mindscout search --source semanticscholar --query "test" -n 5

# If you get results immediately, you're not rate limited
# If you see retry messages, you're hitting the limit
```

### Monitor API Usage

Create a simple wrapper script:
```bash
#!/bin/bash
# save as: check_s2_status.sh

echo "Testing Semantic Scholar API..."
result=$(mindscout search --source semanticscholar --query "test" -n 2 2>&1)

if echo "$result" | grep -q "Rate limit"; then
    echo "❌ Rate limited - wait 5 minutes"
else
    echo "✅ API available"
fi
```

## Troubleshooting

### Still Getting Rate Limited?

**Problem**: Immediate rate limit even after waiting
- **Cause**: Shared IP (VPN, university network, etc.)
- **Solution**: Get an API key (free) or use arXiv

**Problem**: Retries don't help
- **Cause**: Already at limit when starting
- **Solution**: Wait the full 5 minutes, then try

**Problem**: Need large dataset
- **Solution**: Break into multiple sessions over time
  ```bash
  # Day 1: Fetch 50 papers
  # Day 2: Fetch 50 more papers
  # etc.
  ```

### Check Your Request Count

If you suspect you're making too many requests:
```bash
# Check recent Semantic Scholar searches
grep "semanticscholar" ~/.mindscout/mindscout.db

# See how many you've fetched
mindscout list --source semanticscholar | wc -l
```

## Alternative: Use arXiv

If Semantic Scholar rate limits are too restrictive for your use case:

```bash
# Fetch from multiple arXiv categories
mindscout fetch -c cs.AI cs.LG cs.CV cs.CL cs.NE

# No rate limits, reliable, and fast!
```

Then use Mind Scout's semantic search to find what you need:
```bash
# After fetching from arXiv, search semantically
mindscout semantic-search "transformers" --limit 20
```

## Summary: Quick Tips

1. ✅ **Use batches of 10-20** papers per request
2. ✅ **Wait 5-10 seconds** between requests
3. ✅ **Get a free API key** for higher limits
4. ✅ **Use specific queries** to reduce results
5. ✅ **Try arXiv first** for broad exploration
6. ✅ **The fetcher now auto-retries** 3 times with backoff
7. ✅ **Partial results are saved** even if rate limited

## Need Help?

If you continue to have issues:
1. Check `~/.mindscout/` for any errors
2. Verify your internet connection
3. Try arXiv as an alternative
4. Get a Semantic Scholar API key (free)
5. Contact Semantic Scholar support for academic research needs
