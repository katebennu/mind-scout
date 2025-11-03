# Fetch Articles Tool - Quick Guide

The `fetch_articles` tool allows you to ask Claude to automatically fetch new research papers and add them to your Mind Scout library.

## Quick Examples

### Fetch from arXiv
```
"Fetch the latest AI papers from arXiv"
"Get new machine learning papers from arXiv"
"Fetch papers from arXiv categories cs.AI and cs.CV"
```

### Fetch from Semantic Scholar
```
"Fetch papers about transformers from Semantic Scholar"
"Find highly cited papers about diffusion models from 2024"
"Get papers about reinforcement learning with at least 50 citations"
"Search for computer vision papers published in 2023-2024"
```

## What Happens

1. **Claude calls the fetch_articles tool** with your parameters
2. **Papers are fetched** from arXiv or Semantic Scholar
3. **Duplicates are filtered** - only new papers are added
4. **Papers are saved** to your Mind Scout database
5. **Summary is returned** showing how many new papers were added

## Parameters Explained

### source (required)
- `"arxiv"` - Fetch from arXiv RSS feeds (latest papers by category)
- `"semanticscholar"` - Search Semantic Scholar with a query

### For arXiv:
- **categories** (optional): List of categories like `["cs.AI", "cs.LG", "cs.CV", "cs.CL"]`
  - Default: `["cs.AI", "cs.LG", "cs.CV", "cs.CL"]` (AI, Machine Learning, Computer Vision, Computation & Language)

### For Semantic Scholar:
- **query** (required): Your search terms (e.g., "transformers", "diffusion models")
- **limit** (optional): Max papers to fetch (default: 20, max: 100)
- **min_citations** (optional): Only papers with at least this many citations
- **year** (optional): Filter by year ("2024") or range ("2023-2024")

## Advanced Examples

### High-Impact Recent Papers
```
User: "Fetch highly cited papers about transformers from 2024 with at least 100 citations"

Claude will use:
- source: "semanticscholar"
- query: "transformers"
- year: "2024"
- min_citations: 100
```

### Specific arXiv Categories
```
User: "Fetch the latest papers from arXiv categories cs.CV and cs.RO"

Claude will use:
- source: "arxiv"
- categories: ["cs.CV", "cs.RO"]
```

### Broad Topic Search
```
User: "Find me papers about multimodal learning"

Claude will use:
- source: "semanticscholar"
- query: "multimodal learning"
- limit: 20 (default)
```

## Common arXiv Categories

- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision
- `cs.CL` - Computation and Language (NLP)
- `cs.NE` - Neural and Evolutionary Computing
- `cs.RO` - Robotics
- `stat.ML` - Machine Learning (Statistics)

## Response Format

The tool returns a summary like:

```json
{
  "success": true,
  "source": "semanticscholar",
  "query": "transformers",
  "fetched": 20,
  "new_articles": 15,
  "duplicates": 5,
  "message": "Fetched 20 papers from Semantic Scholar, 15 were new",
  "filters": {
    "min_citations": 50,
    "year": "2024"
  }
}
```

## Workflow Integration

You can combine fetch with other tools:

```
User: "Fetch new diffusion model papers, then show me the top 5 recommendations"

Claude will:
1. Use fetch_articles to get papers
2. Use get_recommendations to show top matches
```

## Tips

1. **Be specific with Semantic Scholar** - Better query = better results
2. **Use year filters** for recent work - "2024" or "2023-2024"
3. **Citation filters find quality** - min_citations: 50+ for established work
4. **arXiv is category-based** - Fetch by area, not by query
5. **Check duplicates** - The tool automatically skips papers you already have

## Limitations

- **arXiv**: RSS feeds only (no search queries)
- **Semantic Scholar**: Max 100 results per request
- **Rate limiting**: Semantic Scholar has API rate limits
- **No full text**: Only metadata (title, abstract, authors, etc.)

## Next Steps After Fetching

After fetching papers, you can:
- `"Show me my new unread papers"`
- `"Get recommendations from papers I just fetched"`
- `"Search for papers about [topic]"` (uses semantic search)
- `"Rate paper [ID] as 5 stars"`
