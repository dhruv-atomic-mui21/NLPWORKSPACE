# Enhanced NLP Notepad

This project is an Enhanced NLP Notepad application that provides advanced natural language processing features including grammar checking, sentiment analysis, text completion, and voice-to-text capabilities. It features a modern React frontend with a dark mode theme and a backend NLP pipeline with modular components.

## Features

- Input text analysis with multiple NLP modules:
  - Grammar checking
  - Sentiment analysis (visualized as a pie chart)
  - Text completion
  - Voice-to-text (audio processing)
- Language selection with a wide range of supported languages
- Save and load text files
- Audio file upload and processing
- Dark mode UI with clear, user-friendly interface

## Frontend

- Built with React
- Dark mode theme for comfortable usage
- Sentiment analysis results displayed as an interactive pie chart
- Module selection with checkboxes (voice module unchecked by default)
- File save/load functionality integrated with backend

## Backend

- Modular NLP pipeline implemented in Python
- Modules include grammar, sentiment (using VADER or transformer models), voice, and completion
- Configurable via `config.yaml`
- REST API endpoints for processing text, uploading audio, saving/loading files, and fetching available modules

## Getting Started

### Prerequisites

- Node.js and npm installed (for frontend)
- Python 3.7+ installed (for backend)
- Required Python packages installed (see `requirements.txt`)

### Running the Application

1. **Backend**

   - Navigate to the backend directory.
   - Install dependencies: `pip install -r requirements.txt`
   - Start the backend server:
     ```
     python main.py --server
     ```
   - The backend server will start on `http://localhost:5000`.

2. **Frontend**

   - Navigate to the frontend directory.
   - Install dependencies: `npm install`
   - Start the frontend development server:
     ```
     npm start
     ```
   - The frontend will open in your default browser at `http://localhost:3000`.

### Usage

- Enter or paste text into the input area.
- Select the desired language.
- Choose the NLP modules to apply.
- Click "Process Text" to analyze.
- View results including grammar corrections, sentiment pie chart, and text completions.
- Upload audio files for voice-to-text processing.
- Save your text to a file or load previously saved files.

## Project Structure

- `frontend/` - React frontend source code
- `backend/` (or root) - Python backend source code including `main.py` and NLP modules
- `config.yaml` - Configuration file for backend modules and settings

## Dependencies

- Frontend:
  - React
- Backend:
  - Flask or FastAPI (depending on implementation)
  - NLTK (for VADER sentiment analysis)
  - Transformers and Torch (for transformer-based sentiment analysis)
  - Other NLP libraries as needed

## License

This project is licensed under the MIT License.

## Acknowledgments

- VADER Sentiment Analysis: https://github.com/cjhutto/vaderSentiment
- Hugging Face Transformers: https://huggingface.co/transformers/
- React: https://reactjs.org/
