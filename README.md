# Zoom Recording Processor - Complete Solution

A production-ready Python application for downloading Zoom recordings and processing them with AI-powered transcription and summarization.

## 🚀 Features

### Zoom Recording Download
- 🔐 Automatic password-protected recording access
- 🍪 Cookie and authentication handling
- 📥 Direct MP4 download with progress tracking
- 🔄 Retry logic and error handling

### Video Processing
- 🎥 Key frame extraction from video
- 🎵 Audio extraction to MP3
- 📊 PowerPoint generation from video frames
- 🗣️ Speech-to-text transcription (Azure Speech Services)
- 🤖 AI-powered meeting summarization (Azure OpenAI)
- 📄 Professional Word document generation

### Configuration Management
- 📝 JSON configuration files
- 🌍 Environment variable support
- 🖥️ Command-line overrides
- 🔧 Template generation

## 📁 Project Structure

```
zoom-recording-processor/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── .gitignore                         # Git ignore file
├── .env.template                      # Environment variables template
├── .env                              # Your environment variables (git ignored)
├── config.template.json               # Configuration template
├── config.json                        # Your configuration (git ignored)
│
├── zoom_capture_download_v2.py        # Zoom recording capture & download
├── mp4_processor.py                   # Main MP4 processing script
├── zoom_mp4_pipeline.py               # Integrated pipeline script
├── example_usage.py                   # Example usage script
│
├── utils/                             # Utility modules
│   ├── __init__.py                   # Package initialization
│   ├── config_manager.py             # Configuration management
│   ├── logger_setup.py               # Logging configuration
│   ├── media_processing.py           # Audio/video processing
│   ├── ai_processing.py              # AI and transcription
│   ├── document_generation.py        # PowerPoint and documents
│   ├── word_formatter.py             # Word document formatting
│   ├── zoom_auth.py                  # Zoom authentication
│   ├── zoom_capture.py               # Network capture for Zoom
│   └── zoom_download.py              # Zoom download utilities
│
├── output/                           # Default output directory
│   ├── input/                        # Copy of original files
│   ├── frame_images/                 # Extracted video frames
│   └── outputs/                      # Generated files
│
└── logs/                             # Application logs
```

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd zoom-recording-processor
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up Azure services
You'll need:
- **Azure Speech Services** account for transcription
- **Azure OpenAI** account for summarization

### 4. Configure the application

#### Option A: Environment file (.env) - Recommended
```bash
# Copy template and edit
cp .env.template .env

# Edit with your values
nano .env  # or your preferred editor
```

#### Option B: Configuration file (JSON)
```bash
# Create configuration template
python mp4_processor.py create-template

# Copy and edit with your values
cp config.template.json config.json
nano config.json
```

Example `config.json`:
```json
{
  "azure": {
    "speech_key": "your-speech-key",
    "speech_endpoint": "https://your-resource.cognitiveservices.azure.com",
    "openai_endpoint": "https://your-resource.openai.azure.com/",
    "openai_key": "your-openai-key",
    "model_name": "azure/gpt-4",
    "api_version": "2024-02-15-preview"
  },
  "processing": {
    "extract_frames": false,
    "create_ppt": false,
    "transcribe": true,
    "generate_summary": true,
    "timeout": 30,
    "headless": true
  },
  "output_dir": "output",
  "log_to_file": true,
  "log_dir": "logs"
}
```

#### Option C: System environment variables
```bash
export AZURE_SPEECH_KEY="your-speech-key"
export AZURE_SPEECH_ENDPOINT="https://your-resource.cognitiveservices.azure.com"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_KEY="your-openai-key"
```

## 📖 Usage

### Configuration System

The application uses a flexible configuration system that allows you to:
1. Set defaults once and forget about them
2. Override settings per-run as needed
3. Keep sensitive data secure

**Quick Setup:**
```bash
# 1. Copy and edit the environment template
cp .env.template .env
edit .env  # Add your Azure keys

# 2. Run with defaults
python zoom_mp4_pipeline.py download-and-process \
  --url "https://zoom.us/..." \
  --password "pass" \
  --process

# 3. Override specific settings when needed
python mp4_processor.py process \
  --mp4-path video.mp4 \
  --output-dir special_output \
  --with-frames  # Override default to extract frames
```

### 1. Download and Process Zoom Recording (All-in-One)

```bash
python zoom_mp4_pipeline.py download-and-process \
  --url "https://zoom.us/rec/share/..." \
  --password "recording_password" \
  --process
```

### 2. Download Only

```bash
python zoom_capture_download_v2.py \
  --url "https://zoom.us/rec/share/..." \
  --password "recording_password" \
  --output-dir "./downloads"
```

### 3. Process Existing MP4

```bash
python mp4_processor.py process \
  --mp4-path "./video.mp4" \
  --output-dir "./processed"
```

### 4. Download Using Saved Credentials

```bash
# First capture saves credentials
python zoom_capture_download_v2.py \
  --url "https://zoom.us/rec/share/..." \
  --password "pass" \
  --output-dir "./output"

# Later, download using saved config
python zoom_mp4_pipeline.py download-from-config \
  --config-file "./output/zoom_recording_vars_*.json"
```

### 5. Python API Usage

```python
from zoom_mp4_pipeline import full_pipeline

# Run complete pipeline
results = full_pipeline(
    zoom_url="https://zoom.us/rec/share/...",
    zoom_password="password123",
    config_file="config.json",  # Optional
    output_dir="output"         # Optional
)

# Access results
print(f"Transcript: {results['transcript_txt']}")
print(f"Summary: {results['summary_txt']}")
print(f"Word Doc: {results['docx']}")
```

## 🎯 Command Reference

### Script Overview

| Script | Purpose | Main Commands |
|--------|---------|---------------|
| `zoom_mp4_pipeline.py` | Complete pipeline (download + process) | `download-and-process`, `process-only` |
| `mp4_processor.py` | Process MP4 files only | `process`, `create-template` |
| `zoom_capture_download_v2.py` | Download Zoom recordings only | (single command) |

### zoom_mp4_pipeline.py
```bash
# Main commands
download-and-process    # Download Zoom recording and process it
download-from-config    # Download using saved configuration
process-only           # Process existing MP4 file
create-template        # Create configuration template

# Options
--url, -u              # Zoom recording URL
--password, -p         # Recording password
--config, -c           # Configuration file path
--output-dir, -o       # Output directory
--process              # Process after download
--headless/--no-headless  # Browser headless mode
--with-frames          # Extract video frames
--with-ppt             # Create PowerPoint
```

### mp4_processor.py
```bash
# Main commands
process                # Process MP4 file
create-template        # Create configuration template

# Options
--mp4-path, -i         # Input MP4 file path
--output-dir, -o       # Output directory
--config, -c           # Configuration file path
--no-frames            # Skip frame extraction
--no-ppt               # Skip PowerPoint creation
--no-transcribe        # Skip transcription
--no-summary           # Skip summary generation
--no-log-file          # Disable file logging
--save-config          # Save current configuration
```

### zoom_capture_download_v2.py
```bash
# Options
--url, -u              # Zoom recording URL (required)
--password, -p         # Recording password (required)
--output-dir, -o       # Output directory (default: output)
--output-filename, -f  # Output filename (default: auto)
--headless             # Run browser in headless mode
--timeout, -t          # Timeout in seconds (default: 30)
--debug                # Enable debug mode
```

## 📤 Output Files

```
output/
├── input/
│   └── recording.mp4              # Copy of original video
├── frame_images/
│   ├── frame_0000_001.png        # Extracted frames (optional)
│   ├── frame_0015_002.png
│   └── ...
└── outputs/
    ├── recording.mp3              # Extracted audio
    ├── recording_frames.pptx      # PowerPoint (optional)
    ├── recording_transcript.json  # Raw transcription data
    ├── recording_transcript.txt   # Formatted transcript
    ├── recording_summary.txt      # AI-generated summary
    └── recording.docx            # Complete Word document
```

## ⚙️ Configuration Details

### Configuration Precedence (highest to lowest):
1. Command-line arguments
2. Environment variables (system)
3. Environment variables (.env file)
4. Configuration file (config.json)
5. Default values

### Configuration File Locations:
1. Specified with `--config` flag
2. `config.json` in current directory
3. `~/.zoom_processor/config.json`
4. `/etc/zoom_processor/config.json`

### Environment File Locations (.env):
1. `.env` in current directory
2. `.env.local` in current directory
3. `~/.zoom_processor/.env`

### Available Settings:

#### Azure Settings
- `speech_key`: Azure Speech API key
- `speech_endpoint`: Azure Speech endpoint URL
- `openai_endpoint`: Azure OpenAI endpoint URL
- `openai_key`: Azure OpenAI API key
- `model_name`: Model deployment name
- `api_version`: API version

#### Processing Settings
- `extract_frames`: Extract video frames (default: false)
- `create_ppt`: Create PowerPoint (default: false)
- `transcribe`: Transcribe audio (default: true)
- `generate_summary`: Generate AI summary (default: true)
- `frame_threshold`: Frame change detection threshold (default: 30)
- `max_speakers`: Maximum speakers for diarization (default: 10)
- `timeout`: Download timeout in seconds (default: 30)
- `headless`: Run browser headless (default: true)

#### General Settings
- `output_dir`: Output directory (default: "output")
- `log_to_file`: Enable file logging (default: true)
- `log_dir`: Log directory (default: "logs")

## 🔍 Troubleshooting

### Common Issues

1. **"Azure configuration is incomplete!"**
   - Ensure all Azure credentials are set
   - Check environment variables or config file
   - Run `create-template` to see required fields

2. **"Password field not found"**
   - Recording might not be password-protected
   - Try with `--no-headless` to see browser
   - Check if cookies need to be accepted

3. **"File size exceeds limit"**
   - Azure Speech API limits: 300 MB, 2 hours
   - Consider splitting large files
   - Process audio separately if needed

4. **Download fails**
   - Increase timeout: set higher value in config
   - Check network connection
   - Verify Zoom URL is correct

### Debug Mode

Enable detailed logging:
```bash
# For Zoom download
python zoom_capture_download_v2.py --url "..." --password "..." --debug

# Check logs directory
ls logs/
```

## 🚀 Quick Start Examples

### Example 1: Process a Zoom meeting
```bash
# One command to download and process
python zoom_mp4_pipeline.py download-and-process \
  --url "https://zoom.us/rec/share/AbCdEf..." \
  --password "meet123" \
  --process
```

### Example 2: Batch process existing recordings
```bash
# Process all MP4s in a directory
for file in recordings/*.mp4; do
    python mp4_processor.py process -i "$file"
done
```

### Example 3: Download for later processing
```bash
# Download now
python zoom_capture_download_v2.py \
  --url "https://zoom.us/rec/share/..." \
  --password "pass"

# Process later
python mp4_processor.py process -i "output/*.mp4"
```

