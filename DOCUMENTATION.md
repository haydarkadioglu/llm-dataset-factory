# Dataset Factory - Comprehensive Documentation

## Overview

Dataset Factory is a Python application that generates LLM fine-tuning datasets (JSONL format) from text documents using either Groq or Gemini APIs. It features a Tkinter GUI for easy file selection, model configuration, and progress tracking.

## Project Structure

```
dataset-factory/
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── settings.json             # User settings (auto-created)
├── output/                   # Default output directory
└── src/
    ├── __init__.py
    ├── config.py             # Configuration management
    ├── settings.py           # Settings persistence
    ├── services/
    │   ├── __init__.py
    │   ├── base.py           # LLMService protocol
    │   ├── groq_client.py    # Groq API client
    │   └── gemini_client.py  # Gemini API client
    ├── loaders/
    │   ├── __init__.py
    │   └── document_loader.py # Document reading utilities
    ├── dataset/
    │   ├── __init__.py
    │   └── builder.py        # Dataset generation logic
    └── ui/
        └── app.py            # Tkinter GUI application
```

## Core Components

### 1. Configuration (`src/config.py`)

**Purpose**: Manages API keys and default model settings.

**Key Features**:
- Loads environment variables from `.env` file
- Supports both Groq and Gemini API keys
- Provides default models for each provider

**Usage**:
```python
config = AppConfig.from_env()
# config.groq_api_key
# config.gemini_api_key
# config.default_model (Groq)
# config.default_gemini_model (Gemini)
```

### 2. Settings Persistence (`src/settings.py`)

**Purpose**: Saves user preferences between sessions.

**Stored Settings**:
- Custom prompt text
- Output directory path

**File Location**: `settings.json` in project root

### 3. LLM Services

#### Base Interface (`src/services/base.py`)
Defines the `LLMService` protocol that all providers must implement:
- `generate()`: Basic text generation
- `synthesize_qa_pairs()`: Generate question-answer pairs

#### Groq Service (`src/services/groq_client.py`)
**API**: Groq Chat Completions API
**Features**:
- Retry logic for rate limits and server errors
- JSON response parsing for QA pairs
- Fallback handling for malformed responses

#### Gemini Service (`src/services/gemini_client.py`)
**API**: Google Generative Language API
**Features**:
- REST-based implementation
- Similar retry and error handling as Groq
- Text-only prompt formatting

### 4. Document Loading (`src/loaders/document_loader.py`)

**Supported Formats**:
- `.txt` - Plain text files
- `.md` - Markdown files  
- `.pdf` - PDF files (using pdfplumber)

**Functions**:
- `load_documents(paths)`: Load multiple documents
- `read_text_file(path)`: Read text/markdown files
- `read_pdf_file(path)`: Extract text from PDFs

### 5. Dataset Builder (`src/dataset/builder.py`)

**Core Functionality**:
- **Text Chunking**: Splits documents into manageable pieces (default: 2000 chars)
- **QA Generation**: Uses LLM to create question-answer pairs from chunks
- **JSONL Export**: Saves results in standard fine-tuning format

**Chunking Logic**:
```python
def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    # Splits text by lines, respecting max_chars limit
    # Preserves line boundaries for better context
```

**Output Format**:
```json
{"input": "question", "output": "answer"}
```

### 6. User Interface (`src/ui/app.py`)

**Main Features**:
- File selection (multiple files supported)
- Provider selection (Groq/Gemini)
- Model presets with recommended defaults
- Custom prompt editor
- Output directory selection
- Real-time progress tracking
- Threaded generation (non-blocking UI)

**Model Presets**:
- **Groq**: `openai/gpt-oss-20b`, `openai/gpt-oss-120b` (recommended), `qwen/qwen3-32b`
- **Gemini**: `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-2.0-flash-lite` (recommended)

## How It Works

### 1. Document Processing Pipeline

```
Files Selected → Load Documents → Chunk Text → Generate QA Pairs → Save JSONL
```

1. **File Loading**: Reads selected documents using appropriate loaders
2. **Chunking**: Splits each document into ~2000 character chunks
3. **QA Generation**: For each chunk:
   - Sends to selected LLM provider
   - Generates 3 question-answer pairs (configurable)
   - Handles custom prompts if provided
4. **Export**: Saves all pairs to timestamped JSONL file

### 2. Threading and Progress

- **UI Thread**: Handles user interactions and progress updates
- **Worker Thread**: Performs document processing and API calls
- **Progress Bar**: Updates after each chunk is processed
- **Controls**: Disabled during generation to prevent conflicts

### 3. Error Handling

- **API Errors**: Automatic retry with exponential backoff
- **File Errors**: Graceful handling of unreadable files
- **JSON Parsing**: Fallback to single summary pair if parsing fails
- **Network Issues**: Timeout and retry logic

## Usage Guide

### 1. Setup

```bash
# Clone repository
git clone <repository-url>
cd dataset-factory

# Install dependencies
pip install -r requirements.txt

# Configure API keys
copy .env.example .env
# Edit .env and add your API keys:
# GROQ_API_KEY=your_groq_key_here
# GEMINI_API_KEY=your_gemini_key_here
```

### 2. Running the Application

```bash
python main.py
```

### 3. Using the Interface

1. **Add Files**: Click "Add files" to select documents
2. **Choose Provider**: Select Groq or Gemini
3. **Select Model**: Use presets or enter custom model name
4. **Set Parameters**: Configure pairs per chunk (default: 3)
5. **Custom Prompt** (optional): Add your own prompt template
6. **Output Directory**: Choose where to save results
7. **Generate**: Click "Generate JSONL" to start processing

### 4. Custom Prompts

You can provide a custom prompt that will be prepended to each text chunk:

```
Create educational questions and answers about the following text. Focus on key concepts and practical applications.

TEXT:
[chunk content here]
```

## Configuration Options

### Environment Variables (`.env`)

```bash
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### Settings (`settings.json`)

```json
{
  "prompt": "Your custom prompt here",
  "output_dir": "output"
}
```

### Code Configuration

- **Chunk Size**: Modify `max_chars` in `chunk_text()` function
- **Retry Logic**: Adjust `retries` parameter in service classes
- **Model Defaults**: Change in `AppConfig` class

## API Rate Limits

### Groq
- Free tier: 30 requests/minute
- Paid tiers: Higher limits available

### Gemini
- Free tier: 15 requests/minute
- Paid tiers: Higher limits available

**Note**: The application includes automatic retry logic for rate limit handling.

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure keys are correctly set in `.env` file
2. **File Reading Errors**: Check file permissions and formats
3. **Network Timeouts**: Increase timeout values in service classes
4. **Memory Issues**: Reduce chunk size for large documents

### Debug Mode

Add debug logging by modifying service classes:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Extending the Application

### Adding New Providers

1. Create new service class implementing `LLMService`
2. Add provider to UI dropdown
3. Update configuration as needed

### Adding New File Formats

1. Add reader function in `document_loader.py`
2. Update `load_documents()` function
3. Add file type to UI file dialog

### Custom Chunking Strategies

Modify `chunk_text()` function to implement:
- Sentence-based chunking
- Paragraph-based chunking
- Semantic chunking (requires additional libraries)

## Performance Considerations

- **Chunk Size**: Larger chunks = fewer API calls but more context per call
- **Concurrent Processing**: Currently single-threaded; could be parallelized
- **Memory Usage**: Large documents are processed in chunks to manage memory
- **API Costs**: Each chunk generates multiple QA pairs; monitor usage

## Security Notes

- API keys are stored in `.env` file (not committed to git)
- No data is sent to external services except the selected LLM provider
- Generated datasets are saved locally only

