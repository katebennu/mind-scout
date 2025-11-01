"""Vector database integration for semantic search."""

import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from mindscout.config import DATA_DIR
from mindscout.database import get_session, Article


class VectorStore:
    """Manages vector embeddings and semantic search using ChromaDB."""

    def __init__(self):
        """Initialize vector store with ChromaDB and embedding model."""
        # Create chroma directory
        chroma_path = os.path.join(DATA_DIR, "chroma")
        os.makedirs(chroma_path, exist_ok=True)

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="articles",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

        # Initialize embedding model (lightweight and good quality)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        self.session = get_session()

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def add_article(self, article: Article) -> bool:
        """Add an article to the vector store.

        Args:
            article: Article object to add

        Returns:
            True if added successfully
        """
        try:
            # Create document text from title and abstract
            text = f"{article.title}\n\n{article.abstract or ''}"

            # Generate embedding
            embedding = self.embed_text(text)

            # Add to ChromaDB
            self.collection.add(
                ids=[str(article.id)],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "article_id": article.id,
                    "source": article.source,
                    "title": article.title,
                    "published_date": article.published_date.isoformat() if article.published_date else None,
                }]
            )
            return True

        except Exception as e:
            print(f"Error adding article {article.id} to vector store: {e}")
            return False

    def index_articles(self, limit: Optional[int] = None, force: bool = False) -> int:
        """Index articles in the vector store.

        Args:
            limit: Maximum number of articles to index
            force: Re-index articles that are already indexed

        Returns:
            Number of articles indexed
        """
        # Get existing IDs in vector store
        existing_ids = set()
        if not force:
            try:
                results = self.collection.get()
                existing_ids = set(results['ids'])
            except Exception:
                pass

        # Get articles to index
        query = self.session.query(Article)

        if not force:
            # Only get articles not already in vector store
            if existing_ids:
                query = query.filter(~Article.id.in_([int(id) for id in existing_ids]))

        if limit:
            query = query.limit(limit)

        articles = query.all()

        # Index articles
        indexed = 0
        for article in articles:
            if self.add_article(article):
                indexed += 1

        return indexed

    def find_similar(
        self,
        article_id: int,
        n_results: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """Find articles similar to a given article.

        Args:
            article_id: ID of the article to find similar papers for
            n_results: Number of results to return
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of similar articles with similarity scores
        """
        # Get the query article
        article = self.session.query(Article).filter_by(id=article_id).first()
        if not article:
            return []

        # Create query text
        query_text = f"{article.title}\n\n{article.abstract or ''}"

        # Search for similar articles
        try:
            results = self.collection.query(
                query_embeddings=[self.embed_text(query_text)],
                n_results=n_results + 1,  # +1 because it might include itself
            )

            similar_articles = []
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                # Skip the query article itself
                if int(doc_id) == article_id:
                    continue

                # Convert distance to similarity (cosine distance -> cosine similarity)
                similarity = 1 - distance

                # Filter by minimum similarity
                if similarity < min_similarity:
                    continue

                # Get full article from database
                similar_article = self.session.query(Article).filter_by(id=int(doc_id)).first()
                if similar_article:
                    similar_articles.append({
                        "article": similar_article,
                        "similarity": similarity,
                    })

            return similar_articles[:n_results]

        except Exception as e:
            print(f"Error finding similar articles: {e}")
            return []

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Perform semantic search for articles.

        Args:
            query: Natural language search query
            n_results: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of articles with relevance scores
        """
        try:
            # Generate embedding for query
            query_embedding = self.embed_text(query)

            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filters if filters else None,
            )

            search_results = []
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                similarity = 1 - distance

                # Get full article from database
                article = self.session.query(Article).filter_by(id=int(doc_id)).first()
                if article:
                    search_results.append({
                        "article": article,
                        "relevance": similarity,
                    })

            return search_results

        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector store.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_indexed": count,
                "model": self.model.get_sentence_embedding_dimension(),
                "collection_name": self.collection.name,
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total_indexed": 0}

    def close(self):
        """Close database session."""
        self.session.close()
