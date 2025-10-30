# Mind Scout - Phase 2 Demo

## What's New in Phase 2

Phase 2 adds **AI-powered content analysis** using Anthropic's Claude 3.5 Haiku model. Your articles are now automatically summarized and categorized!

### ✨ New Features

1. **Smart Summarization** - 2-sentence summaries of research papers
2. **Topic Extraction** - Automatic keyword/topic identification
3. **Batch Processing** - Process multiple articles efficiently
4. **Topic Search** - Find articles by topic
5. **Processing Stats** - Track your analysis progress

---

## Setup

### 1. Get an Anthropic API Key

Visit https://console.anthropic.com/ and create an API key.

### 2. Set Environment Variable

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### 3. Migrate Database

If upgrading from Phase 1:

```bash
python migrate_db_phase2.py
```

---

## Demo Walkthrough

### Step 1: Check Processing Status

```bash
mindscout processing-stats
```

Output:
```
   Processing Statistics
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric          ┃ Value ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Articles  │   436 │
│ Processed       │     0 │
│ Unprocessed     │   436 │
│ Processing Rate │  0.0% │
└─────────────────┴───────┘
```

### Step 2: Process Some Articles

Start with a small batch to test:

```bash
mindscout process --limit 5
```

Output:
```
Processing up to 5 articles...
✓ Processed 5 articles
```

What happens during processing:
- Claude reads the article title and abstract
- Generates a 2-sentence summary
- Extracts 3-5 key topics
- Creates a vector embedding (for future semantic search)
- Stores everything in the database

### Step 3: View Discovered Topics

```bash
mindscout topics
```

Output:
```
        Top Topics
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Topic               ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Machine Learning    │    15 │
│ Neural Networks     │    12 │
│ Computer Vision     │    10 │
│ Natural Language    │     8 │
│ Reinforcement       │     6 │
└─────────────────────┴───────┘

Total unique topics: 45
```

### Step 4: Find Articles by Topic

```bash
mindscout find-by-topic "transformer"
```

Output:
```
       Articles matching 'transformer' (8 found)
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ ID   ┃ Title                          ┃ Topics             ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 42   │ Attention Is All You Need 2.0  │ Transformers, N... │
│ 87   │ Vision Transformers for CV     │ Computer Vision... │
│ 133  │ Transformer Optimization       │ Training, Optim... │
└──────┴────────────────────────────────┴────────────────────┘
```

### Step 5: View Processed Article

```bash
mindscout show 42
```

Output now includes:
```
╭─────────────────────── Article 42 ───────────────────────╮
│ Title: Attention Is All You Need 2.0                     │
│ Authors: Smith et al.                                    │
│ Source: arxiv (2510.12345)                               │
│ Published: 2025-10-15                                    │
│ URL: https://arxiv.org/abs/2510.12345                    │
│ Categories: cs.LG                                        │
│ Status: Unread                                           │
│                                                          │
│ Summary: (NEW!)                                          │
│ This paper introduces an improved Transformer            │
│ architecture that achieves 40% faster training while     │
│ maintaining SOTA performance. The method uses sparse     │
│ attention and dynamic routing for efficiency.            │
│                                                          │
│ Topics: (NEW!)                                           │
│ Transformers, Attention Mechanisms, Neural Architecture  │
│                                                          │
│ Abstract:                                                │
│ [Full abstract follows...]                               │
╰──────────────────────────────────────────────────────────╯
```

### Step 6: Process Everything

Once you're confident it works:

```bash
mindscout process
```

This will process all remaining articles. For 436 articles:
- Time: ~10-20 minutes
- Cost: ~$2-5 (with Haiku's pricing)
- Result: Fully analyzed collection

---

## New CLI Commands

### `mindscout process`

Process unprocessed articles with LLM.

**Options:**
- `--limit N` - Process at most N articles
- `--force` - Reprocess already processed articles

**Examples:**
```bash
# Process 10 articles
mindscout process --limit 10

# Process all unprocessed
mindscout process

# Reprocess everything (e.g., after model upgrade)
mindscout process --force
```

### `mindscout topics`

Show all discovered topics across processed articles.

**Example:**
```bash
mindscout topics
```

### `mindscout find-by-topic <topic>`

Search for articles matching a topic.

**Options:**
- `--limit N` - Show at most N results (default: 10)

**Examples:**
```bash
# Find articles about diffusion models
mindscout find-by-topic "diffusion"

# Find up to 20 RL papers
mindscout find-by-topic "reinforcement" --limit 20
```

### `mindscout processing-stats`

Show processing progress statistics.

**Example:**
```bash
mindscout processing-stats
```

---

## Cost Estimates

Using Claude 3.5 Haiku (recommended for Phase 2):

| Articles | Est. Cost | Time   |
|----------|-----------|--------|
| 10       | $0.05     | 30s    |
| 100      | $0.50     | 5min   |
| 500      | $2.50     | 20min  |
| 1000     | $5.00     | 40min  |

Costs are approximate. Haiku is optimized for high throughput and cost-effectiveness.

### Cost Control Tips

1. **Start small**: Test with `--limit 5` first
2. **Use Haiku**: Claude 3.5 Haiku is 10x cheaper than Sonnet
3. **Don't reprocess**: Only use `--force` when necessary
4. **Batch wisely**: Process in chunks during testing

---

## Technical Details

### Model Used

**Claude 3.5 Haiku** (`claude-3-5-haiku-20241022`)

Why Haiku?
- ✅ Fast (2-3x faster than Sonnet)
- ✅ Cost-effective (10x cheaper)
- ✅ Still very capable for summarization and classification
- ✅ Good enough for Phase 2 (we can upgrade to Sonnet in Phase 3 if needed)

### Processing Pipeline

For each article:
1. **Summarize**: Generate 2-sentence summary from abstract
2. **Extract Topics**: Identify 3-5 key technical topics
3. **Embed**: Create vector embedding (placeholder for Phase 5)
4. **Store**: Save results to database with processed=True flag

### Database Changes

New columns in `articles` table:
```sql
summary TEXT              -- LLM-generated summary
topics TEXT               -- JSON array of topics
embedding TEXT            -- JSON array (768-dim vector)
processed BOOLEAN         -- Processing status
processing_date DATETIME  -- When processed
```

### Embedding Note

Phase 2 uses a placeholder embedding system (deterministic hash-based). In Phase 5, we'll integrate a proper embedding model (Voyage AI, OpenAI Ada, or similar) for semantic search.

---

## Troubleshooting

### Error: "Anthropic API key not found"

**Solution:**
```bash
export ANTHROPIC_API_KEY='your-key'
```

### Error: "no such column: articles.summary"

**Solution:** Run migration:
```bash
python migrate_db_phase2.py
```

### Processing is slow

**Expected:** Each article takes ~1-2 seconds with Haiku. 100 articles = 2-3 minutes.

**If slower:** Check your internet connection.

### Want to see what Claude generates?

Processed data is stored in the database. View with:
```bash
mindscout show <article_id>
```

Or query directly:
```bash
sqlite3 ~/.mindscout/mindscout.db "SELECT id, title, summary FROM articles WHERE processed=1 LIMIT 5"
```

---

## Next Steps

### Use Your Processed Collection

Now that articles are processed:
1. Browse by topic: `mindscout find-by-topic <your-interest>`
2. Read summaries instead of full abstracts
3. Discover patterns in your reading

### Prepare for Phase 3

Phase 3 will add:
- Personal interest tracking
- Smart recommendations based on your reading
- Feedback learning (thumbs up/down)
- Reading history analytics

With processed topics, Phase 3 can immediately start making intelligent recommendations!

---

## Portfolio Value

### What Phase 2 Demonstrates

**Technical Skills:**
- ✅ LLM API integration (Anthropic)
- ✅ Prompt engineering for summarization and classification
- ✅ Database migrations
- ✅ Batch processing with error handling
- ✅ Cost-aware design (using Haiku vs Sonnet)

**System Design:**
- ✅ Lazy initialization for optional features
- ✅ Graceful degradation (stats work without API key)
- ✅ Modular architecture (processors/ package)
- ✅ Data persistence and state management

**Product Thinking:**
- ✅ Clear user value (summaries save time)
- ✅ Cost consideration (Haiku for efficiency)
- ✅ Progressive enhancement (Phase 1 still works)
- ✅ Foundation for Phase 3 recommendations

---

**Phase 2 Complete!** 🎉

You now have an AI-powered research assistant that automatically analyzes and categorizes papers. Ready for Phase 3? Check [PROJECT_PLAN.md](PROJECT_PLAN.md) for the next steps!
