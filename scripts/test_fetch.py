#!/usr/bin/env python
"""Test script to verify fetch functionality."""

from mindscout.database import Article, get_session
from mindscout.fetchers.arxiv import fetch_arxiv

print("Before fetch:")
session = get_session()
count_before = session.query(Article).count()
print(f"  Articles in DB: {count_before}")
session.close()

print("\nFetching from cs.CV (Computer Vision)...")
new_articles = fetch_arxiv(["cs.CV"])
print(f"  New articles fetched: {new_articles}")

print("\nAfter fetch:")
session = get_session()
count_after = session.query(Article).count()
print(f"  Articles in DB: {count_after}")
print(f"  Net change: +{count_after - count_before}")
session.close()

print("\n✓ Fetch test completed successfully!")
