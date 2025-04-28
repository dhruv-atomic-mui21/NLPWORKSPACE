"""
Grammar checker module using external LanguageTool server.
"""
import logging
from typing import Dict, List, Any, Optional
import language_tool_python

from .core import ProcessorModule

logger = logging.getLogger(__name__)

class GrammarChecker(ProcessorModule):
    """Check grammar and spelling in text using LanguageTool HTTP server."""

    @property
    def name(self) -> str:
        return "grammar"

    @property
    def supported_languages(self) -> List[str]:
        return ["en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "pt-PT"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        config = config or {}
        self.language = config.get("language", "en-US")  # Fixed: Default to string instead of trying to instantiate List
        if self.language not in self.supported_languages:
            logger.warning(f"Language '{self.language}' is not supported. Defaulting to 'en-US'.")
            self.language = "en-US"
        self.tool = None
        self.server_url = config.get("server_url", "http://localhost:8081")  # Made server URL configurable

        try:
            # Initialize LanguageTool to connect to your running server
            self.tool = language_tool_python.LanguageTool(self.language, remote_server=self.server_url)
            logger.info(f"GrammarChecker initialized with LanguageTool server at {self.server_url} for language {self.language}")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool server: {str(e)}")
            self.tool = None

    def process(self, text: str, **kwargs) -> Dict[str, Any]:
        """Check text for grammar and spelling issues."""
        if not self.tool:
            logger.warning("GrammarChecker is not initialized. Returning text without checks.")
            return {
                "issues_count": 0,
                "issues": [],
                "corrected_text": text
            }

        try:
            # Use the language specified during initialization
            matches = self.tool.check(text)

            issues = []
            for match in matches:
                issues.append({
                    "message": match.message,
                    "offset": match.offset,
                    "length": match.errorLength,
                    "rule_id": match.ruleId,
                    "replacements": match.replacements[:5],
                })

            corrected_text = language_tool_python.utils.correct(text, matches)

            return {
                "issues_count": len(issues),
                "issues": issues,
                "corrected_text": corrected_text
            }

        except Exception as e:
            logger.error(f"Error during grammar checking: {str(e)}")
            return {
                "issues_count": 0,
                "issues": [],
                "corrected_text": text
            }