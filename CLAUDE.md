# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (required for media processing)
# Ubuntu/Debian: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html
```

### Running the Application

**Basic Usage - Download and Process a Zoom Recording:**
```bash
# Download a Zoom recording
python src/zoom_capture_download.py --url "https://zoom.us/rec/share/..." --password "password"

# Process the downloaded MP4
python src/mp4_processor.py process --mp4-path ./output/downloaded.mp4

# Or use the basic usage example for combined workflow
python examples/basic_usage.py --url "https://zoom.us/rec/share/..." --password "password"
```

**Configuration:**
```bash
# Create configuration from template
cp config.json.template config.json
# Then edit config.json with Azure credentials

# Validate configuration
python src/mp4_processor.py validate-config

# Create a new configuration template
python src/mp4_processor.py create-template
```

### Development Commands

**Running Scripts with Debug Mode:**
```bash
# Enable debug logging for any script
python src/zoom_capture_download.py --url "..." --debug
python src/mp4_processor.py process --mp4-path "..." --debug
```

**Note:** This codebase does not currently have automated tests, linting, or build commands configured. When implementing new features, consider adding appropriate testing infrastructure.

## High-Level Architecture

### Two-Stage Processing Pipeline

The system operates in two distinct stages:

**Stage 1: Zoom Download (Browser Automation)**
- Entry point: `src/zoom_capture_download.py`
- Uses nodriver (undetected Chrome) for stealth browser automation
- Handles authentication, password protection, and cookie consent
- Captures network requests to extract MP4 download URLs
- Downloads files with retry logic and progress tracking

**Stage 2: MP4 Processing (AI Pipeline)**
- Entry point: `src/mp4_processor.py`
- Orchestrates multiple processing steps:
  1. Media extraction (audio/video frames)
  2. Azure Speech Services transcription with speaker diarization
  3. Azure OpenAI summarization via modular LLM client
  4. Document generation (Word, PowerPoint, transcripts)

### Key Architectural Decisions

**Modular LLM Client Design:**
- Located in `src/utils/mp4_processing/azure_client.py`
- Uses litellm for provider-agnostic interface
- Easy to extend with new providers (OpenAI, Anthropic, etc.)
- Centralized prompts in `src/utils/mp4_processing/prompts.py`

**Configuration Hierarchy:**
- CLI arguments override environment variables
- Environment variables override config.json
- config.json overrides built-in defaults
- Managed by `src/utils/config_manager.py` with type-safe dataclasses

**Separation of Concerns:**
- Each major function is a standalone class
- Can run stages independently or as integrated pipeline
- Clear interfaces between components for easy testing/mocking

### Important Implementation Details

**Browser Automation Resilience:**
- Cookie persistence for session reuse
- Automatic retry on network failures
- Handles dynamic content loading and redirects

**Media Processing Constraints:**
- Azure Speech API limit: 300MB audio files
- Frame detection uses histogram analysis with configurable thresholds
- Audio converted to 48kHz mono for optimal transcription

**Error Handling:**
- Centralized logging with rotation (`src/utils/logger_setup.py`)
- Progress bars for long operations using tqdm
- Graceful degradation when optional features fail

### Extension Points

**Adding New LLM Providers:**
1. Create new client in `src/utils/mp4_processing/`
2. Implement same interface as `AzureLLMClient`
3. Update `AIProcessor` to use new client based on config

**Custom Document Templates:**
1. Extend `WordDocFormatter` in `src/utils/mp4_processing/word_formatter.py`
2. Override styling methods for corporate branding
3. Update `DocumentGenerator` to use custom formatter

**Platform Support:**
1. Download modules in `src/utils/zoom_download/` are Zoom-specific
2. Create similar modules for other platforms (Webex, Teams, etc.)
3. Update main entry point to route based on URL pattern