"""
Text completion module using Nvidia's API or HuggingFace models.
"""
import logging
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
load_dotenv("credintials.env")

from .core import ProcessorModule

logger = logging.getLogger(__name__)

class TextCompletion(ProcessorModule):
    """Generate text completions using large language models."""
    
    @property
    def name(self) -> str:
        return "completion"
    
    @property
    def supported_languages(self) -> List[str]:
        # Most LLMs support multiple languages
        return ["en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "it-IT", "pt-PT", "ru-RU", "zh-CN", "ja-JP"]
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the text completion model."""
        config = config or {}
        self.provider = config.get("provider", "nvidia")  # 'nvidia' or 'huggingface'
        self.model_name = config.get("model_name", "nv-mistralai/mistral-nemo-12b-instruct")
        self.api_key = config.get("api_key", os.environ.get("NVIDIA_API_KEY"))
        self.max_tokens = config.get("max_tokens", 100)
        self.base_url = config.get("base_url", "https://integrate.api.nvidia.com/v1")
        self.temperature = config.get("temperature", 0.2)
        self.top_p = config.get("top_p", 0.7)
        self.stream = config.get("stream", False)
        self.client = None
        self.model = None
        
        try:
            if self.provider == "nvidia":
                # Import OpenAI library for Nvidia API
                from openai import OpenAI
                
                if not self.api_key:
                    raise ValueError("Nvidia API key is required")
                
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                logger.info(f"Nvidia client initialized with model {self.model_name}")
                
            elif self.provider == "huggingface":
                # Import transformer libraries
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                logger.info(f"Loading HuggingFace model: {self.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    self.model = self.model.to("cuda")
                    logger.info("Model moved to GPU")
                
                logger.info("HuggingFace model loaded successfully")
                
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
                
        except ImportError as e:
            if self.provider == "nvidia":
                logger.error("Cannot import OpenAI library. Install with: pip install openai")
            else:
                logger.error("Cannot import transformers. Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize text completion: {str(e)}")
            raise RuntimeError(f"Could not initialize text completion: {str(e)}") from e
    
    def process(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate text completion for the input text."""
        if (self.provider == "nvidia" and not self.client) or \
           (self.provider == "huggingface" and (not self.tokenizer or not self.model)):
            raise RuntimeError("TextCompletion not properly initialized")
            
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        top_p = kwargs.get("top_p", self.top_p)
        stream = kwargs.get("stream", self.stream)
        
        try:
            if self.provider == "nvidia":
                # Use Nvidia API for completion
                completion_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. Complete the text appropriately."},
                        {"role": "user", "content": text}
                    ],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=stream
                )
                
                if stream:
                    # Handle streaming response
                    completion_parts = []
                    for chunk in completion_response:
                        if chunk.choices[0].delta.content is not None:
                            completion_parts.append(chunk.choices[0].delta.content)
                            
                    completion = "".join(completion_parts)
                    
                    # No direct access to token usage in streaming mode
                    return {
                        "completion": completion,
                        "tokens_used": None  # Tokens not tracked in streaming mode
                    }
                else:
                    # Handle regular response
                    completion = completion_response.choices[0].message.content
                    
                    return {
                        "completion": completion,
                        "tokens_used": completion_response.usage.total_tokens if hasattr(completion_response, 'usage') else None
                    }
                
            else:  # huggingface
                import torch
                
                # Tokenize and prepare input
                inputs = self.tokenizer(text, return_tensors="pt")
                
                # Move to same device as model
                if torch.cuda.is_available():
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
                # Generate text
                with torch.no_grad():
                    output = self.model.generate(
                        **inputs,
                        max_length=len(inputs["input_ids"][0]) + max_tokens,
                        num_return_sequences=1,
                        no_repeat_ngram_size=2,
                        do_sample=True,
                        top_p=top_p,
                        top_k=50,
                        temperature=temperature
                    )
                
                # Decode the output
                generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
                
                # Extract only the newly generated part
                completion = generated_text[len(text):]
                
                return {
                    "completion": completion,
                    "tokens_used": len(output[0])
                }
                
        except Exception as e:
            logger.error(f"Error during text completion: {str(e)}")
            raise RuntimeError(f"Could not generate text completion: {str(e)}") from e