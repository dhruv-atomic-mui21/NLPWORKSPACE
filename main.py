#!/usr/bin/env python
"""
Enhanced NLP Notepad - Main application entry point.
"""
import os
import sys
import logging
import argparse
import yaml
from typing import Dict, Any

# Import pipeline
from modules.core import Pipeline

import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nlp_notepad.log")
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file {config_path} not found. Using defaults.")
            return {}
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

def create_pipeline(config: Dict[str, Any]) -> Pipeline:
    """Create and initialize the NLP pipeline."""
    pipe = Pipeline()
    
    # Get enabled modules from config or default to all known module names
    enabled_modules = config.get("enabled_modules", [
        "grammar",
        "sentiment",
        "voice",
        "completion"
    ])
    
    # Map module names to their class names and module paths
    module_info = {
        "grammar": ("modules.grammar", "GrammarChecker"),
        "sentiment": ("modules.sentiment", "SentimentAnalyzer"),
        "voice": ("modules.voice", "VoiceToText"),
        "completion": ("modules.completion", "TextCompletion")
    }
    
    for mod_name in enabled_modules:
        if mod_name in module_info:
            mod_path, class_name = module_info[mod_name]
            try:
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, class_name)
                instance = cls()
                pipe.register(instance)
                logger.info(f"Registered module: {mod_name}")
            except Exception as e:
                logger.error(f"Failed to load/register module {mod_name}: {str(e)}")
        else:
            logger.warning(f"Module {mod_name} not recognized and will be skipped.")
    
    # Initialize the pipeline with module-specific configurations
    try:
        pipe.initialize_all(config.get("modules", {}))
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {str(e)}")
        sys.exit(1)
        
    return pipe

def process_text(pipeline: Pipeline, text: str, language: str = "en-US") -> Dict[str, Any]:
    """Process text through the NLP pipeline."""
    try:
        return pipeline.run_all(text, language=language)
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return {"error": str(e)}

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description='Enhanced NLP Notepad')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--text', help='Text to process')
    parser.add_argument('--file', help='Text file to process')
    parser.add_argument('--language', default='en-US', help='Language code (e.g., en-US, fr-FR)')
    parser.add_argument('--server', action='store_true', help='Start the web server interface')
    args = parser.parse_args()
    
    config = load_config(args.config)
    pipeline = create_pipeline(config)
    
    if args.server:
        # Start web server
        from server import start_server
        start_server(pipeline, config.get("server", {}))
        return
    
    # Process text from file or argument
    text = None
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        print("Please provide text using --text or --file options, or start the server with --server")
        sys.exit(1)
    
    # Process the text and print results
    results = process_text(pipeline, text, args.language)
    
    print("\n=== NLP Analysis Results ===\n")
    for module_name, result in results.items():
        print(f"\n--- {module_name.upper()} ---")
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (list, dict)):
                    print(f"{key}:")
                    print(f"{value}")
                else:
                    print(f"{key}: {value}")
        else:
            print(result)

if __name__ == "__main__":
    main()