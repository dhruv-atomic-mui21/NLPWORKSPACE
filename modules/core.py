"""
Core pipeline implementation for modular NLP processing.
"""
import logging
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessorModule(ABC):
    """Base abstract class for all processor modules."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the module's unique name."""
        pass
    
    @property
    def supported_languages(self) -> List[str]:
        """Return a list of supported language codes."""
        return ["en-US"]  # Default to English
    
    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the module with config options."""
        pass
    
    @abstractmethod
    def process(self, text: str, **kwargs) -> Any:
        """Process input text and return results."""
        pass
    
    def can_process(self, language: str) -> bool:
        """Check if this module supports the given language."""
        return language in self.supported_languages


class Pipeline:
    """Main pipeline orchestrator for text processing modules."""
    
    def __init__(self):
        self.modules: Dict[str, ProcessorModule] = {}
        self.config: Dict[str, Dict[str, Any]] = {}
        self.initialized = False
        logger.info("NLP Pipeline created")
    
    def register(self, module: ProcessorModule) -> None:
        """Register a processor module with the pipeline."""
        if module.name in self.modules:
            logger.warning(f"Module '{module.name}' is already registered. Overwriting.")
        self.modules[module.name] = module
        logger.info(f"Registered module: {module.name}")
    
    def unregister(self, module_name: str) -> bool:
        """Remove a processor module from the pipeline."""
        if module_name in self.modules:
            del self.modules[module_name]
            logger.info(f"Unregistered module: {module_name}")
            return True
        logger.warning(f"Cannot unregister '{module_name}': module not found")
        return False
    
    def initialize_all(self, config: Dict[str, Dict[str, Any]] = None) -> None:
        """Initialize all registered modules with their configurations."""
        self.config = config or {}
        
        for name, module in self.modules.items():
            try:
                module_config = self.config.get(name, {})
                module.initialize(module_config)
                logger.info(f"Initialized module: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize module '{name}': {str(e)}")
                raise RuntimeError(f"Module initialization failed: {name}") from e
        
        self.initialized = True
        logger.info("Pipeline initialization complete")
    
    def run_module(self, module_name: str, text: str, **kwargs) -> Any:
        """Run a specific module on the input text."""
        if not self.initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize_all() first.")
            
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' not found in pipeline")
        
        module = self.modules[module_name]
        language = kwargs.get('language', 'en-US')
        
        if not module.can_process(language):
            logger.warning(f"Module {module_name} doesn't support language '{language}'. Skipping.")
            return None
            
        try:
            return module.process(text, **kwargs)
        except Exception as e:
            logger.error(f"Error in module '{module_name}': {str(e)}")
            raise
    
    def run_all(self, text: str, **kwargs) -> Dict[str, Any]:
        """Run all modules on the input text and collect results."""
        if not self.initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize_all() first.")
            
        results = {}
        language = kwargs.get('language', 'en-US')
        
        for name, module in self.modules.items():
            if not module.can_process(language):
                logger.info(f"Skipping module '{name}' that doesn't support language '{language}'")
                continue
                
            try:
                results[name] = module.process(text, **kwargs)
                logger.debug(f"Successfully ran module: {name}")
            except Exception as e:
                logger.error(f"Error running module '{name}': {str(e)}")
                results[name] = {"error": str(e)}
                
        return results