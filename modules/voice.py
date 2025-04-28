"""
Voice-to-text conversion module using speech recognition.
"""
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional

from .core import ProcessorModule

logger = logging.getLogger(__name__)

class VoiceToText(ProcessorModule):
    """Convert voice audio to text using various speech recognition APIs."""
    
    @property
    def name(self) -> str:
        return "voice"
    
    @property
    def supported_languages(self) -> List[str]:
        return ["en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "ja-JP", "zh-CN"]
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the voice-to-text converter."""
        config = config or {}
        self.api_key = config.get("api_key", os.environ.get("SPEECH_API_KEY"))
        self.provider = config.get("provider", "google")  # 'google' or 'whisper'
        self.recognizer = None
        
        try:
            if self.provider == "google":
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                logger.info("Google speech recognition initialized")
                
            elif self.provider == "whisper":
                # Check if we have OpenAI whisper
                try:
                    import whisper
                    self.whisper_model = whisper.load_model("base")
                    logger.info("OpenAI Whisper model loaded")
                except ImportError:
                    logger.error("Cannot import whisper. Install with: pip install openai-whisper")
                    raise
                    
            else:
                raise ValueError(f"Unknown voice provider: {self.provider}")
                
        except ImportError as e:
            logger.error("Cannot import speech_recognition. Install with: pip install SpeechRecognition")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize voice-to-text: {str(e)}")
            raise RuntimeError(f"Could not initialize voice-to-text: {str(e)}") from e
    
    def process(self, audio_data_or_path: Any, **kwargs) -> Dict[str, Any]:
        """
        Convert audio to text.
        
        Parameters:
        - audio_data_or_path: Can be a path to an audio file or raw audio data
        - kwargs: Additional parameters like language
        
        Returns:
        - Dictionary with transcribed text and confidence score
        """
        if self.provider == "google" and not self.recognizer:
            raise RuntimeError("Voice-to-text not properly initialized")
            
        language = kwargs.get("language", "en-US")
        
        try:
            if self.provider == "google":
                import speech_recognition as sr
                
                # Check if input is a file path or audio data
                if isinstance(audio_data_or_path, str):
                    # It's a file path
                    with sr.AudioFile(audio_data_or_path) as source:
                        audio_data = self.recognizer.record(source)
                else:
                    # Assume it's already audio data
                    audio_data = audio_data_or_path
                
                # Perform the speech recognition
                result = self.recognizer.recognize_google(
                    audio_data,
                    language=language,
                    show_all=True,
                    key=self.api_key
                )
                
                # Extract text and confidence
                if result and "alternative" in result:
                    text = result["alternative"][0]["transcript"]
                    confidence = result["alternative"][0].get("confidence", 0.0)
                else:
                    text = ""
                    confidence = 0.0
                    
                return {
                    "text": text,
                    "confidence": confidence
                }
                
            elif self.provider == "whisper":
                # For Whisper, we need a file path
                if not isinstance(audio_data_or_path, str):
                    # If it's not a path, save to temp file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    # Save the audio data to the temp file
                    # This depends on the format of audio_data_or_path
                    # and might need adjustments based on your use case
                    with open(temp_path, 'wb') as f:
                        f.write(audio_data_or_path)
                        
                    audio_path = temp_path
                else:
                    audio_path = audio_data_or_path
                
                # Use Whisper to transcribe
                result = self.whisper_model.transcribe(audio_path)
                
                # Clean up temp file if needed
                if not isinstance(audio_data_or_path, str):
                    os.unlink(temp_path)
                    
                return {
                    "text": result["text"],
                    "confidence": 0.9  # Whisper doesn't provide confidence scores by default
                }
                
        except Exception as e:
            logger.error(f"Error during voice-to-text conversion: {str(e)}")
            raise