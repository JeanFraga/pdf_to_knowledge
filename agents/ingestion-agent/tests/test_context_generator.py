"""
Unit Tests for Global Context Generation Module

Tests cover:
- GlobalContext and KeyTerm Pydantic models
- Prompt template formatting
- Gemini response parsing
- Error handling and edge cases
- Mock Gemini API calls

Story: 3.1 - Global Context Generation
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.context_generator import (
    ContextGenerator,
    GlobalContext,
    KeyTerm,
    GLOBAL_CONTEXT_PROMPT,
    generate_global_context,
)


class TestKeyTerm:
    """Tests for KeyTerm Pydantic model."""
    
    def test_valid_key_term(self):
        """Test creating a valid KeyTerm."""
        term = KeyTerm(
            term="neural network",
            definition="A computing system inspired by biological neural networks",
        )
        
        assert term.term == "neural network"
        assert "computing system" in term.definition
        assert term.frequency is None
    
    def test_key_term_with_frequency(self):
        """Test KeyTerm with frequency count."""
        term = KeyTerm(
            term="backpropagation",
            definition="Algorithm for training neural networks by computing gradients",
            frequency=42,
        )
        
        assert term.frequency == 42
    
    def test_key_term_definition_too_short(self):
        """Test that definition must be at least 10 characters."""
        with pytest.raises(ValueError):
            KeyTerm(
                term="test",
                definition="short",  # Less than 10 chars
            )
    
    def test_key_term_invalid_frequency(self):
        """Test that frequency must be >= 1 if provided."""
        with pytest.raises(ValueError):
            KeyTerm(
                term="test",
                definition="A valid definition here",
                frequency=0,
            )


class TestGlobalContext:
    """Tests for GlobalContext Pydantic model."""
    
    def test_valid_global_context(self):
        """Test creating a valid GlobalContext."""
        context = GlobalContext(
            summary="This is a comprehensive summary of the document that explains the main concepts and themes covered throughout. It provides context for understanding individual sections.",
            document_type="textbook",
            key_terms=[
                KeyTerm(term="concept", definition="A fundamental idea or principle")
            ],
            main_themes=["machine learning", "data science", "statistics"],
            target_audience="data scientists",
            source_document="ml_textbook.pdf",
        )
        
        assert context.document_type == "textbook"
        assert len(context.key_terms) == 1
        assert len(context.main_themes) == 3
        assert context.target_audience == "data scientists"
        assert context.generated_at is not None
    
    def test_global_context_defaults(self):
        """Test GlobalContext with minimal required fields."""
        context = GlobalContext(
            summary="A" * 100,  # Minimum 100 chars
            document_type="unknown",
            main_themes=["theme1"],
        )
        
        assert context.key_terms == []
        assert context.target_audience is None
        assert context.source_document == ""
        assert context.token_count is None
    
    def test_global_context_summary_too_short(self):
        """Test that summary must be at least 100 characters."""
        with pytest.raises(ValueError):
            GlobalContext(
                summary="Too short",
                document_type="test",
                main_themes=["theme"],
            )
    
    def test_global_context_generated_at_auto(self):
        """Test that generated_at is automatically set."""
        before = datetime.now(timezone.utc)
        context = GlobalContext(
            summary="A" * 100,
            document_type="test",
            main_themes=["theme"],
        )
        after = datetime.now(timezone.utc)
        
        assert before <= context.generated_at <= after


class TestContextGenerator:
    """Tests for ContextGenerator class."""
    
    @pytest.fixture
    def mock_api_key(self, monkeypatch):
        """Set up mock API key in environment."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
    
    @pytest.fixture
    def generator(self, mock_api_key):
        """Create a ContextGenerator instance with mocked client."""
        with patch('src.context_generator.genai.Client'):
            return ContextGenerator()
    
    def test_init_with_env_api_key(self, mock_api_key):
        """Test initialization with environment API key."""
        with patch('src.context_generator.genai.Client') as mock_client:
            gen = ContextGenerator()
            assert gen.model == "gemini-2.0-flash"
            mock_client.assert_called_once_with(api_key="test-api-key")
    
    def test_init_with_custom_model(self, mock_api_key):
        """Test initialization with custom model."""
        with patch('src.context_generator.genai.Client'):
            gen = ContextGenerator(model="gemini-1.5-pro")
            assert gen.model == "gemini-1.5-pro"
    
    def test_init_with_explicit_api_key(self):
        """Test initialization with explicit API key."""
        with patch('src.context_generator.genai.Client') as mock_client:
            gen = ContextGenerator(api_key="explicit-key")
            mock_client.assert_called_once_with(api_key="explicit-key")
    
    def test_init_missing_api_key(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="API key required"):
            ContextGenerator()
    
    def test_estimate_tokens(self, generator):
        """Test token estimation."""
        # 400 characters ~= 100 tokens
        text = "a" * 400
        tokens = generator._estimate_tokens(text)
        assert tokens == 100
    
    def test_generate_empty_text(self, generator):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="too short"):
            generator.generate("")
    
    def test_generate_short_text(self, generator):
        """Test that very short text raises ValueError."""
        with pytest.raises(ValueError, match="too short"):
            generator.generate("Short text")
    
    def test_parse_response_valid_json(self, generator):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "summary": "A" * 100,
            "document_type": "textbook",
            "key_terms": [
                {"term": "concept", "definition": "A fundamental idea or principle"}
            ],
            "main_themes": ["theme1", "theme2"],
            "target_audience": "developers",
        })
        
        context = generator._parse_response(response)
        
        assert context.document_type == "textbook"
        assert len(context.key_terms) == 1
        assert context.key_terms[0].term == "concept"
    
    def test_parse_response_with_markdown(self, generator):
        """Test parsing response wrapped in markdown code blocks."""
        response = '''```json
{
    "summary": "''' + "A" * 100 + '''",
    "document_type": "manual",
    "key_terms": [],
    "main_themes": ["theme"],
    "target_audience": null
}
```'''
        
        context = generator._parse_response(response)
        assert context.document_type == "manual"
    
    def test_parse_response_invalid_json(self, generator):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse"):
            generator._parse_response("not valid json {{{")
    
    @patch('src.context_generator.genai.Client')
    def test_generate_full_flow(self, mock_client_class, mock_api_key):
        """Test full generation flow with mocked Gemini."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "summary": "This is a comprehensive summary of the machine learning textbook covering neural networks, deep learning, and optimization techniques. " * 3,
            "document_type": "textbook",
            "key_terms": [
                {"term": "neural network", "definition": "A computing model inspired by biological neurons"},
                {"term": "gradient descent", "definition": "An optimization algorithm for finding minimum values"},
            ],
            "main_themes": ["machine learning", "neural networks", "optimization"],
            "target_audience": "data scientists and ML engineers",
        })
        
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        generator = ContextGenerator()
        result = generator.generate(
            full_text="A" * 200,  # Enough text
            source_document="test.pdf",
        )
        
        assert isinstance(result, GlobalContext)
        assert result.document_type == "textbook"
        assert len(result.key_terms) == 2
        assert result.source_document == "test.pdf"
        assert result.token_count is not None
    
    @patch('src.context_generator.genai.Client')
    def test_generate_retries_on_failure(self, mock_client_class, mock_api_key):
        """Test that generation retries on API failure."""
        mock_client = MagicMock()
        
        # First two calls fail, third succeeds
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "summary": "A" * 100,
            "document_type": "test",
            "key_terms": [],
            "main_themes": ["theme"],
        })
        
        mock_client.models.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_response,
        ]
        mock_client_class.return_value = mock_client
        
        generator = ContextGenerator()
        result = generator.generate("A" * 200)
        
        assert result.document_type == "test"
        assert mock_client.models.generate_content.call_count == 3
    
    @patch('src.context_generator.genai.Client')
    def test_generate_fails_after_max_retries(self, mock_client_class, mock_api_key):
        """Test that generation fails after max retries."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Persistent error")
        mock_client_class.return_value = mock_client
        
        generator = ContextGenerator()
        
        with pytest.raises(RuntimeError, match="Failed to generate context"):
            generator.generate("A" * 200)
        
        assert mock_client.models.generate_content.call_count == 3


class TestPromptTemplate:
    """Tests for the prompt template."""
    
    def test_prompt_contains_placeholders(self):
        """Test that prompt template has expected structure."""
        assert "{full_text}" in GLOBAL_CONTEXT_PROMPT
        assert "summary" in GLOBAL_CONTEXT_PROMPT
        assert "document_type" in GLOBAL_CONTEXT_PROMPT
        assert "key_terms" in GLOBAL_CONTEXT_PROMPT
        assert "main_themes" in GLOBAL_CONTEXT_PROMPT
    
    def test_prompt_formatting(self):
        """Test that prompt can be formatted with text."""
        sample_text = "This is sample document text."
        formatted = GLOBAL_CONTEXT_PROMPT.format(full_text=sample_text)
        
        assert sample_text in formatted
        assert "{full_text}" not in formatted


class TestConvenienceFunction:
    """Tests for generate_global_context convenience function."""
    
    def test_convenience_function_missing_api_key(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="API key required"):
            generate_global_context("Some text here" * 20)
    
    @patch('src.context_generator.genai.Client')
    def test_convenience_function_works(self, mock_client_class, monkeypatch):
        """Test convenience function with mocked client."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "summary": "A" * 100,
            "document_type": "guide",
            "key_terms": [],
            "main_themes": ["topic"],
        })
        
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        result = generate_global_context(
            full_text="A" * 200,
            source_document="doc.pdf",
        )
        
        assert isinstance(result, GlobalContext)
        assert result.document_type == "guide"


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def mock_api_key(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    
    @patch('src.context_generator.genai.Client')
    def test_empty_gemini_response(self, mock_client_class, mock_api_key):
        """Test handling of empty Gemini response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = None
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        generator = ContextGenerator()
        
        with pytest.raises(RuntimeError, match="Failed to generate"):
            generator.generate("A" * 200)
    
    @patch('src.context_generator.genai.Client')
    def test_partial_json_response(self, mock_client_class, mock_api_key):
        """Test handling of partial/incomplete JSON."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"summary": "incomplete...'
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        generator = ContextGenerator()
        
        with pytest.raises(ValueError, match="Failed to parse"):
            generator.generate("A" * 200)
    
    def test_gemini_api_key_fallback(self, monkeypatch):
        """Test that GEMINI_API_KEY is used as fallback."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-fallback-key")
        
        with patch('src.context_generator.genai.Client') as mock_client:
            ContextGenerator()
            mock_client.assert_called_once_with(api_key="gemini-fallback-key")
