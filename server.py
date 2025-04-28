"""
Web server implementation for the NLP Notepad using Flask.
"""
import os
import logging
import tempfile
import json
from typing import Dict, Any
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

from modules.core import Pipeline

logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_folder="static",
            template_folder="template")


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_text():
    """Process text through the NLP pipeline."""
    if not global_pipeline:
        return jsonify({"error": "Server not properly initialized"}), 500
    
    # Get text from request
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    text = data['text']
    language = data.get('language', 'en-US')
    modules = data.get('modules', None)  # Optional specific modules to run
    
    try:
        if modules:
            # Run specific modules only
            results = {}
            for module_name in modules:
                if module_name in global_pipeline.modules:
                    results[module_name] = global_pipeline.run_module(module_name, text, language=language)
                else:
                    results[module_name] = {"error": f"Module {module_name} not found"}
        else:
            # Run all modules
            results = global_pipeline.run_all(text, language=language)
            
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/modules', methods=['GET'])
def get_modules():
    """Get list of available modules."""
    if not global_pipeline:
        return jsonify({"error": "Server not properly initialized"}), 500
    
    modules = list(global_pipeline.modules.keys())
    return jsonify({"modules": modules})

@app.route('/api/upload_audio', methods=['POST'])
def upload_audio():
    """Handle audio file upload for voice-to-text conversion."""
    if not global_pipeline or 'voice' not in global_pipeline.modules:
        return jsonify({"error": "Voice-to-text module not available"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        file.save(temp_path)
        language = request.form.get('language', 'en-US')
        
        # Process with voice module
        result = global_pipeline.run_module('voice', temp_path, language=language)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return jsonify({"error": str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save_text():
    """Save text to a file."""
    data = request.get_json()
    if not data or 'text' not in data or 'filename' not in data:
        return jsonify({"error": "Text and filename are required"}), 400
    
    text = data['text']
    filename = secure_filename(data['filename'])
    
    try:
        # Ensure the uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        
        file_path = os.path.join('uploads', filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        return jsonify({"success": True, "path": file_path})
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/load', methods=['GET'])
def list_files():
    """List saved files."""
    try:
        if not os.path.exists('uploads'):
            return jsonify({"files": []})
            
        files = [f for f in os.listdir('uploads') if os.path.isfile(os.path.join('uploads', f))]
        return jsonify({"files": files})
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/load/<filename>', methods=['GET'])
def load_file(filename):
    """Load text from a file."""
    filename = secure_filename(filename)
    file_path = os.path.join('uploads', filename)
    
    try:
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        return jsonify({"text": text})
    except Exception as e:
        logger.error(f"Error loading file: {str(e)}")
        return jsonify({"error": str(e)}), 500

def start_server(pipeline: Pipeline, config: Dict[str, Any] = None):
    """Start the web server with the given pipeline."""
    global global_pipeline
    global_pipeline = pipeline
    
    config = config or {}
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 5000)
    debug = config.get('debug', False)
    
    logger.info(f"Starting NLP Notepad web server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)