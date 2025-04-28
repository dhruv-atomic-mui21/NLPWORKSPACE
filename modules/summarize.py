"""
Text summarization module using transformer models.
"""
import logging
from typing import Dict, List, Any, Optional

from .core import ProcessorModule

logger = logging.getLogger(__name__)

class Summarizer(ProcessorModule):
    """Text summarization using Hugging Face transformer models."""
    
    @property
    def name(self) -> str:
        return "summarize"
    
    @property
    def supported_languages(self) -> List[str]:
        # The languages depend on the model used
        return ["en-US", "en-GB"]  # Default supports English
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the summarization model."""
        config = config or {}
        self.model_name = config.get("model_name", "facebook/bart-large-cnn")
        self.max_length = config.get("max_length", 150)
        self.min_length = config.get("min_length", 30)
        self.model = None
        self.tokenizer = None
        
        try:
            # Import here to avoid dependency if not used
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            
            logger.info(f"Loading summarization model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            logger.info("Summarization model loaded successfully")
        except ImportError:
            logger.error("Cannot import transformers library. Install with: pip install transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load summarization model: {str(e)}")
            raise RuntimeError(f"Could not initialize summarization model: {str(e)}") from e
    
    def process(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate a summary of the input text."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Summarizer not properly initialized")
            
        # Override config with kwargs if provided
        max_length = kwargs.get("max_length", self.max_length)
        min_length = kwargs.get("min_length", self.min_length)
        
        try:
            # Skip summarization for very short texts
            if len(text.split()) < min_length:
                logger.info(f"Text too short ({len(text.split())} words). Skipping summarization.")
                return {
                    "summary": text,
                    "original_length": len(text),
                    "summary_length": len(text),
                    "compression_ratio": 1.0
                }
            
            # Prepare the text for the model
            inputs = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
            
            # Generate summary
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
            
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            # Calculate compression stats
            return {
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
                "compression_ratio": len(summary) / len(text) if len(text) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            raise