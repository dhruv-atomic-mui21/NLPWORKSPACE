"""
Sentiment analysis module using VADER and transformer models.
"""
import logging
from typing import Dict, List, Any, Optional

from .core import ProcessorModule

logger = logging.getLogger(__name__)

class SentimentAnalyzer(ProcessorModule):
    """Analyze sentiment in text using VADER and/or transformer models."""
    
    @property
    def name(self) -> str:
        return "sentiment"
    
    @property
    def supported_languages(self) -> List[str]:
        # VADER primarily supports English
        # For other languages, you would need a different model
        return ["en-US", "en-GB"]
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the sentiment analyzer."""
        config = config or {}
        self.analyzer_type = config.get("analyzer", "vader")  # 'vader' or 'transformer'
        self.transformer_model = config.get("model_name", "distilbert-base-uncased-finetuned-sst-2-english")
        self.vader_analyzer = None
        self.transformer_tokenizer = None
        self.transformer_model_instance = None
        
        try:
            if self.analyzer_type == "vader":
                # Import NLTK's VADER
                from nltk.sentiment.vader import SentimentIntensityAnalyzer
                import nltk
                
                try:
                    # Download VADER lexicon if needed
                    nltk.data.find('sentiment/vader_lexicon.zip')
                except LookupError:
                    logger.info("Downloading VADER lexicon")
                    nltk.download('vader_lexicon')
                
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("VADER sentiment analyzer initialized")
                
            elif self.analyzer_type == "transformer":
                # Import transformer libraries
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                import torch
                
                logger.info(f"Loading sentiment model: {self.transformer_model}")
                self.transformer_tokenizer = AutoTokenizer.from_pretrained(self.transformer_model)
                self.transformer_model_instance = AutoModelForSequenceClassification.from_pretrained(self.transformer_model)
                logger.info("Transformer sentiment model loaded successfully")
                
            else:
                raise ValueError(f"Unknown sentiment analyzer type: {self.analyzer_type}")
                
        except ImportError as e:
            if self.analyzer_type == "vader":
                logger.error("Cannot import NLTK. Install with: pip install nltk")
            else:
                logger.error("Cannot import transformers. Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {str(e)}")
            raise RuntimeError(f"Could not initialize sentiment analyzer: {str(e)}") from e
    
    def process(self, text: str, **kwargs) -> Dict[str, Any]:
        """Analyze sentiment in the input text."""
        # Make sure we're initialized
        if (self.analyzer_type == "vader" and not self.vader_analyzer) or \
           (self.analyzer_type == "transformer" and (not self.transformer_tokenizer or not self.transformer_model_instance)):
            raise RuntimeError("SentimentAnalyzer not properly initialized")
            
        try:
            if self.analyzer_type == "vader":
                # Use VADER for sentiment analysis
                scores = self.vader_analyzer.polarity_scores(text)
                
                # Determine overall sentiment
                if scores['compound'] >= 0.05:
                    sentiment = "positive"
                elif scores['compound'] <= -0.05:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                    
                return {
                    "scores": scores,
                    "sentiment": sentiment
                }
                
            else:  # transformer
                import torch
                
                # Tokenize and prepare input
                inputs = self.transformer_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                
                # Get prediction
                with torch.no_grad():
                    outputs = self.transformer_model_instance(**inputs)
                    
                # Get scores and convert to probabilities
                scores = torch.nn.functional.softmax(outputs.logits, dim=1)
                
                # Convert to regular dict (depends on the specific model's output labels)
                # This assumes a binary classification model (positive/negative)
                result = {
                    "positive": float(scores[0][1]),
                    "negative": float(scores[0][0])
                }
                
                # Determine sentiment
                sentiment = "positive" if result["positive"] > result["negative"] else "negative"
                if abs(result["positive"] - result["negative"]) < 0.2:
                    sentiment = "neutral"
                    
                return {
                    "scores": result,
                    "sentiment": sentiment
                }
                
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {str(e)}")
            raise