#!/usr/bin/env python
"""Script for testing article processing (not a pytest test).

Run manually with: python tests/script_process.py
"""

import os

# Check for API key
if not os.getenv("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY environment variable not set")
    print("\nTo set it:")
    print("  export ANTHROPIC_API_KEY='your-api-key-here'")
    print("\nOr get a key from: https://console.anthropic.com/")
    exit(1)

from mindscout.processors.content import ContentProcessor

print("Testing article processing with Anthropic Claude...\n")

# Create processor
processor = ContentProcessor()

# Process just 3 articles as a test
print("Processing 3 articles...")
processed, failed = processor.process_batch(limit=3, force=False)

print(f"\n✓ Processed: {processed}")
print(f"✗ Failed: {failed}")

# Show stats
print("\nProcessing Statistics:")
stats = processor.get_processing_stats()
print(f"  Total: {stats['total_articles']}")
print(f"  Processed: {stats['processed']}")
print(f"  Rate: {stats['processing_rate']:.1f}%")

if stats["top_topics"]:
    print("\nTop Topics Discovered:")
    for topic, count in stats["top_topics"][:5]:
        print(f"  - {topic}: {count}")

print("\n✓ Test complete!")
print("\nTo process more articles, run:")
print("  mindscout process --limit 10")
print("\nTo process all articles:")
print("  mindscout process")
