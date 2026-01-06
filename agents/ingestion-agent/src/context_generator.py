"""
Global Context Generation Module

Generates a comprehensive summary of an entire document to provide
context for individual chunks during retrieval.

Features:
- 1-2 page summary capturing key themes and purpose
- Key term extraction with definitions
- Document type classification
- Large context window support (up to 500 pages via Gemini 2.5 Flash)

Story: 3.1 - Global Context Generation
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class KeyTerm(BaseModel):
    """A key term extracted from the document with its definition."""
    
    term: str = Field(
        ...,
        description="The key term or concept",
        examples=["neural network", "backpropagation"]
    )
    definition: str = Field(
        ...,
        description="Brief definition or explanation of the term",
        min_length=10
    )
    frequency: Optional[int] = Field(
        default=None,
        description="Approximate number of times the term appears",
        ge=1
    )
    
    model_config = {"extra": "forbid"}


class GlobalContext(BaseModel):
    """
    Global context summary for a document.
    
    This summary is injected into individual chunks to provide
    readers with understanding of how each chunk relates to the whole.
    """
    
    summary: str = Field(
        ...,
        description="1-2 page comprehensive summary of the document",
        min_length=100
    )
    document_type: str = Field(
        ...,
        description="Classification of the document type",
        examples=["textbook", "technical manual", "research paper", "user guide"]
    )
    key_terms: list[KeyTerm] = Field(
        default_factory=list,
        description="List of key terms and their definitions"
    )
    main_themes: list[str] = Field(
        default_factory=list,
        description="3-5 main themes or topics covered",
        min_length=1
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Inferred target audience for the document",
        examples=["software developers", "data scientists", "general readers"]
    )
    source_document: str = Field(
        default="",
        description="Original document filename or identifier"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the context was generated"
    )
    token_count: Optional[int] = Field(
        default=None,
        description="Approximate token count of the source text"
    )
    
    model_config = {"extra": "forbid"}


# Prompt template for global context generation
GLOBAL_CONTEXT_PROMPT = """You are analyzing a technical document to create a global context summary.

Your task is to produce a JSON object with the following structure:
{{
    "summary": "A comprehensive 1-2 page summary of the document, focusing on main themes, purpose, and key information. This summary will be used to provide context to isolated chunks extracted from this document, helping readers understand each chunk in relation to the whole.",
    "document_type": "The type of document (e.g., textbook, technical manual, research paper, user guide, API documentation, tutorial)",
    "key_terms": [
        {{
            "term": "technical term or concept",
            "definition": "clear, concise definition (at least 10 characters)",
            "frequency": null
        }}
    ],
    "main_themes": ["theme1", "theme2", "theme3"],
    "target_audience": "The intended audience for this document"
}}

Guidelines:
1. The summary should be detailed enough (1-2 pages worth) to give full context
2. Identify 10-20 key terms that are essential to understanding the document
3. List 3-5 main themes that recur throughout the document
4. Infer the target audience based on language complexity and assumed knowledge
5. Be specific and factual - do not make up information not present in the document

Document text:
{full_text}

Respond with ONLY the JSON object, no additional text."""


class ContextGenerator:
    """
    Generates global context summaries for documents using Gemini.
    
    Uses Gemini 2.5 Flash for large context window support (1M tokens),
    enabling processing of documents up to ~500 pages.
    """
    
    # Default model with large context window
    DEFAULT_MODEL = "gemini-2.0-flash"
    
    # Token estimation: ~750 tokens per page
    TOKENS_PER_PAGE = 750
    
    # Maximum retry attempts for API calls
    MAX_RETRIES = 3
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the context generator.
        
        Args:
            model: Gemini model to use (default: gemini-2.0-flash)
            api_key: Google API key (defaults to GOOGLE_API_KEY or GEMINI_API_KEY env var)
        """
        self.model = model or os.getenv("CONTEXT_GENERATOR_MODEL", self.DEFAULT_MODEL)
        
        # Get API key from parameter or environment
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "API key required. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable, "
                "or pass api_key parameter."
            )
        
        # Initialize client
        self._client = genai.Client(api_key=self._api_key)
    
    def generate(
        self,
        full_text: str,
        source_document: str = "",
    ) -> GlobalContext:
        """
        Generate global context for a document.
        
        Args:
            full_text: The complete extracted text from the document
            source_document: Optional filename or identifier for the source
            
        Returns:
            GlobalContext object with summary, key terms, themes, etc.
            
        Raises:
            ValueError: If text is empty or too short
            RuntimeError: If API call fails after retries
        """
        if not full_text or len(full_text.strip()) < 100:
            raise ValueError("Document text is too short to generate meaningful context")
        
        # Estimate token count
        estimated_tokens = self._estimate_tokens(full_text)
        
        # Generate context via Gemini
        prompt = GLOBAL_CONTEXT_PROMPT.format(full_text=full_text)
        
        response_text = self._call_gemini(prompt)
        
        # Parse response into GlobalContext
        context = self._parse_response(response_text)
        
        # Add metadata
        context.source_document = source_document
        context.generated_at = datetime.now(timezone.utc)
        context.token_count = estimated_tokens
        
        return context
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses a simple heuristic: ~4 characters per token on average.
        """
        return len(text) // 4
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API with retry logic.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response text from Gemini
            
        Raises:
            RuntimeError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,  # Lower temperature for more consistent output
                        max_output_tokens=4096,
                    ),
                )
                
                if response.text:
                    return response.text
                else:
                    raise RuntimeError("Empty response from Gemini")
                    
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    # Could add exponential backoff here
                    continue
        
        raise RuntimeError(f"Failed to generate context after {self.MAX_RETRIES} attempts: {last_error}")
    
    def _parse_response(self, response_text: str) -> GlobalContext:
        """
        Parse Gemini response into GlobalContext object.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            GlobalContext object
            
        Raises:
            ValueError: If response cannot be parsed
        """
        # Clean up response - remove markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
        
        # Convert to GlobalContext
        try:
            # Parse key terms
            key_terms = []
            for term_data in data.get("key_terms", []):
                key_terms.append(KeyTerm(
                    term=term_data.get("term", ""),
                    definition=term_data.get("definition", "No definition provided"),
                    frequency=term_data.get("frequency"),
                ))
            
            return GlobalContext(
                summary=data.get("summary", ""),
                document_type=data.get("document_type", "unknown"),
                key_terms=key_terms,
                main_themes=data.get("main_themes", []),
                target_audience=data.get("target_audience"),
            )
        except Exception as e:
            raise ValueError(f"Failed to construct GlobalContext from response: {e}")


def generate_global_context(
    full_text: str,
    source_document: str = "",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> GlobalContext:
    """
    Convenience function to generate global context for a document.
    
    Args:
        full_text: The complete extracted text from the document
        source_document: Optional filename or identifier
        model: Optional Gemini model override
        api_key: Optional API key override
        
    Returns:
        GlobalContext object with summary, key terms, themes, etc.
    """
    generator = ContextGenerator(model=model, api_key=api_key)
    return generator.generate(full_text, source_document)
