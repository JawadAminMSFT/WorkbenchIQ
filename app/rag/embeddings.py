"""
Embedding Service - Generates vector embeddings via Azure OpenAI.

Uses the text-embedding-3-small model (1536 dimensions) by default.
Supports batch processing with retry logic and exponential backoff.
Supports both API key and Azure AD (Managed Identity) authentication.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from app.config import OpenAISettings, RAGSettings
from app.utils import setup_logging

logger = setup_logging()


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class EmbeddingService:
    """
    Service for generating text embeddings using Azure OpenAI.
    
    Supports:
    - Single text embedding
    - Batch embedding (up to 100 texts)
    - Retry with exponential backoff
    - Azure AD authentication (preferred) or API key authentication
    """
    
    # Azure OpenAI batch limit
    MAX_BATCH_SIZE = 100
    
    # Azure OpenAI cognitive services scope for Azure AD auth
    AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
    
    def __init__(
        self,
        openai_settings: OpenAISettings,
        rag_settings: RAGSettings | None = None,
        embedding_deployment: str | None = None,
        use_azure_ad: bool = True,
    ):
        """
        Initialize the embedding service.
        
        Args:
            openai_settings: Azure OpenAI configuration
            rag_settings: RAG configuration (for model/dimensions)
            embedding_deployment: Optional deployment name override for embeddings
            use_azure_ad: If True, use Azure AD auth; if False, use API key
        """
        self.settings = openai_settings
        self.rag_settings = rag_settings or RAGSettings()
        self.use_azure_ad = use_azure_ad
        
        # Use embedding-specific deployment: explicit override > RAG settings > error
        self.embedding_deployment = (
            embedding_deployment 
            or self.rag_settings.embedding_deployment
        )
        
        if not self.embedding_deployment:
            raise EmbeddingError(
                "No embedding deployment configured. "
                "Set EMBEDDING_DEPLOYMENT environment variable to your Azure OpenAI embedding model deployment name."
            )
        
        # Model configuration
        self.model = self.rag_settings.embedding_model
        self.dimensions = self.rag_settings.embedding_dimensions
        
        # Initialize Azure AD credential if using Azure AD auth
        self._credential = None
        self._token_provider = None
        if self.use_azure_ad:
            try:
                self._credential = DefaultAzureCredential()
                self._token_provider = get_bearer_token_provider(
                    self._credential, 
                    self.AZURE_OPENAI_SCOPE
                )
                logger.info("EmbeddingService initialized with Azure AD authentication")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure AD auth, falling back to API key: {e}")
                self.use_azure_ad = False
        
        if not self.use_azure_ad:
            logger.info("EmbeddingService initialized with API key authentication")
    
    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for Azure OpenAI API."""
        headers = {"Content-Type": "application/json"}
        
        if self.use_azure_ad and self._token_provider:
            try:
                token = self._token_provider()
                headers["Authorization"] = f"Bearer {token}"
                return headers
            except Exception as e:
                logger.warning(f"Azure AD token acquisition failed, falling back to API key: {e}")
        
        # Fallback to API key
        if self.settings.api_key:
            headers["api-key"] = self.settings.api_key
        else:
            raise EmbeddingError(
                "No authentication available. Either configure Azure AD credentials "
                "or set AZURE_OPENAI_API_KEY environment variable."
            )
        
        return headers
    
    def get_embedding(
        self,
        text: str,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            max_retries: Number of retry attempts
            retry_backoff: Exponential backoff multiplier
            
        Returns:
            Embedding vector (list of floats)
            
        Raises:
            EmbeddingError: If embedding generation fails after retries
        """
        embeddings = self.get_embeddings_batch(
            [text],
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )
        return embeddings[0]
    
    def get_embeddings_batch(
        self,
        texts: list[str],
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed (max 100)
            max_retries: Number of retry attempts
            retry_backoff: Exponential backoff multiplier
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails after retries
        """
        if not texts:
            return []
        
        if len(texts) > self.MAX_BATCH_SIZE:
            raise EmbeddingError(
                f"Batch size {len(texts)} exceeds maximum {self.MAX_BATCH_SIZE}. "
                "Split into smaller batches."
            )
        
        # Validate settings
        if not self.settings.endpoint:
            raise EmbeddingError(
                "Azure OpenAI endpoint not configured. "
                "Set AZURE_OPENAI_ENDPOINT environment variable."
            )
        
        # Build request
        url = f"{self.settings.endpoint}/openai/deployments/{self.embedding_deployment}/embeddings"
        params = {"api-version": self.settings.api_version}
        headers = self._get_auth_headers()
        payload = {
            "input": texts,
            "model": self.model,
        }
        
        # Add dimensions if not default (for newer models)
        if self.dimensions and self.dimensions != 1536:
            payload["dimensions"] = self.dimensions
        
        # Execute with retry
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    params=params,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Extract embeddings in order
                    embeddings_data = sorted(
                        data.get("data", []),
                        key=lambda x: x.get("index", 0)
                    )
                    embeddings = [item["embedding"] for item in embeddings_data]
                    
                    if len(embeddings) != len(texts):
                        raise EmbeddingError(
                            f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                        )
                    
                    logger.debug(f"Generated {len(embeddings)} embeddings")
                    return embeddings
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", retry_backoff ** attempt))
                    logger.warning(f"Rate limited, retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Other errors
                error_msg = response.text[:500]
                last_error = EmbeddingError(
                    f"Embedding API error {response.status_code}: {error_msg}"
                )
                
                # Don't retry client errors (4xx except 429)
                if 400 <= response.status_code < 500:
                    raise last_error
                
            except requests.exceptions.Timeout:
                last_error = EmbeddingError("Embedding API timeout")
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: Timeout")
            except requests.exceptions.RequestException as e:
                last_error = EmbeddingError(f"Network error: {e}")
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: {e}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                sleep_time = retry_backoff ** attempt
                logger.debug(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
        
        raise last_error or EmbeddingError("Embedding generation failed")
    
    def embed_chunks(
        self,
        chunks: list[Any],
        batch_size: int = 50,
    ) -> list[Any]:
        """
        Generate embeddings for PolicyChunk objects.
        
        Modifies chunks in-place by setting their embedding attribute.
        
        Args:
            chunks: List of PolicyChunk objects
            batch_size: Number of chunks to process per batch
            
        Returns:
            Same list of chunks with embeddings populated
        """
        from app.rag.chunker import PolicyChunk
        
        if not chunks:
            return chunks
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]
            
            logger.info(f"Embedding batch {i // batch_size + 1} ({len(texts)} chunks)...")
            embeddings = self.get_embeddings_batch(texts)
            
            # Assign embeddings to chunks
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding
        
        logger.info(f"Generated embeddings for {len(chunks)} chunks")
        return chunks
