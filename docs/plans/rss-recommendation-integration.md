# Plan: Full RSS Integration with Recommendation System

## Summary
Integrate RSS articles fully into the recommendation system with:
1. Topic extraction for RSS articles via ContentProcessor
2. CLI command for background feed polling
3. Interest-based notifications created after processing

## Current State
- RSS articles are fetched and stored in the Article table with `source="rss"`
- ContentProcessor exists and works on any article source
- Notification table has `type` field supporting `new_article` and `interest_match`
- RSSFeed table has `check_interval` field (unused)
- CLI has `mindscout fetch` and `mindscout process` commands

## Implementation Steps

### Step 1: Add CLI Command for Feed Refresh
**File: `mindscout/cli.py`**

Add `mindscout refresh-feeds` command:
```python
@app.command()
def refresh_feeds():
    """Refresh all active RSS feed subscriptions."""
    from mindscout.fetchers.rss import RSSFetcher
    fetcher = RSSFetcher()
    result = fetcher.refresh_all_feeds()
    print(f"Checked {result['feeds_checked']} feeds")
    print(f"New articles: {result['new_count']}")
```

This leverages existing `RSSFetcher.refresh_all_feeds()` method.

### Step 2: Ensure RSS Articles Are Processed
**File: `mindscout/processors/content.py`**

The ContentProcessor already works on all articles. Verify it processes RSS articles:
- `process_batch()` queries unprocessed articles regardless of source
- No changes needed, just run `mindscout process` after `mindscout refresh-feeds`

### Step 3: Add Interest-Based Notifications
**File: `mindscout/processors/content.py`**

After topic extraction, check if topics match user interests and create notifications:

```python
def _create_interest_notification(self, article: Article, session):
    """Create notification if article topics match user interests."""
    from mindscout.database import UserProfile, Notification

    profile = session.query(UserProfile).first()
    if not profile or not profile.interests:
        return

    user_interests = set(i.strip().lower() for i in profile.interests.split(','))
    article_topics = set(t.strip().lower() for t in (article.topics or '').split(','))

    if user_interests & article_topics:  # If any overlap
        notification = Notification(
            article_id=article.id,
            type="interest_match"
        )
        session.add(notification)
```

Call this after successful topic extraction in `process_article()`.

### Step 4: Update Notification Types Display
**File: `frontend/src/pages/Notifications.jsx`**

Display interest-match notifications differently:
- Show "Matches your interests" badge for `type="interest_match"`
- Show matched topics if available

### Step 5: Add RSS to Preferred Sources (Optional)
**File: `backend/api/profile.py`**

Ensure "rss" is a valid preferred source option. The recommendation engine already respects `preferred_sources`.

## Files to Modify
1. `mindscout/cli.py` - Add `refresh-feeds` command
2. `mindscout/processors/content.py` - Add interest notification creation after processing
3. `frontend/src/pages/Notifications.jsx` - Display interest-match notification type
4. `backend/api/profile.py` - (Optional) Validate "rss" as preferred source

## Usage Flow
```bash
# Refresh RSS feeds (run via cron every N minutes)
mindscout refresh-feeds

# Process new articles (extracts topics, creates interest notifications)
mindscout process --limit 50

# Or combine into single cron job:
mindscout refresh-feeds && mindscout process
```

## Testing
1. Subscribe to an RSS feed via UI or API
2. Run `mindscout refresh-feeds` to fetch articles
3. Run `mindscout process` to extract topics
4. Check that interest-match notifications are created for matching articles
5. Verify RSS articles appear in recommendations when topics match user interests
