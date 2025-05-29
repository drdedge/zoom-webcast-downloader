# Zoom Recording Processor

A comprehensive tool for capturing, downloading, and processing Zoom recordings. This tool can:
- Capture Zoom recording credentials and download MP4 files
- Generate transcripts using Azure AI Services
- Extract key frames when slides change
- Create timestamped PowerPoint presentations
- Generate Word documents with summaries

## Features

- 🎥 **Automated Zoom Recording Download**: Bypass password protection and download recordings
- 📝 **AI-Powered Transcription**: Generate accurate transcripts using Azure Speech Services
- 🖼️ **Smart Frame Extraction**: Detect and capture slide changes automatically
- 📊 **Document Generation**: Create Word summaries and PowerPoint presentations
- 🔐 **Secure Credential Handling**: Safe password and authentication management

## Prerequisites

- Python 3.8+
- FFmpeg installed on your system
- Azure Cognitive Services account (for transcription)
- Chrome/Chromium browser

## Installation

1. Clone the repository:
```bash
git clone https://github.com/drdedge/zoom-webcast-downloader.git
cd zoom-webcast-downloader
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

## Usage

### Basic Usage

Download a Zoom recording:
```bash
python src/zoom_capture_download.py --url "YOUR_ZOOM_URL" --password "YOUR_PASSWORD"
```

### Advanced Usage

Download and process a recording:
```bash
# Download with custom output
python src/zoom_capture_download.py \
    --url "YOUR_ZOOM_URL" \
    --password "YOUR_PASSWORD" \
    --output-dir "./my_recordings" \
    --output-filename "meeting_2024.mp4" \
    --headless

# Process the downloaded recording
python src/zoom_processor.py \
    --input "./my_recordings/meeting_2024.mp4" \
    --generate-transcript \
    --extract-frames \
    --create-ppt \
    --create-summary
```

### Command Line Options

#### zoom_capture_download.py
- `--url`: Zoom recording URL (required)
- `--password`: Recording password (required)
- `--output-dir`: Output directory (default: ./output)
- `--output-filename`: Output filename (default: auto-generated)
- `--headless`: Run browser in headless mode
- `--timeout`: Timeout in seconds (default: 30)

#### zoom_processor.py
- `--input`: Input MP4 file path
- `--generate-transcript`: Generate transcript
- `--extract-frames`: Extract key frames
- `--create-ppt`: Create PowerPoint presentation
- `--create-summary`: Create Word document summary
- `--azure-key`: Azure Speech API key (or use .env)
- `--azure-region`: Azure region (or use .env)

## Configuration

Create a `.env` file with your Azure credentials:
```env
AZURE_SPEECH_KEY=your_speech_key_here
AZURE_SPEECH_REGION=your_region_here
AZURE_TEXT_ANALYTICS_KEY=your_text_analytics_key_here
AZURE_TEXT_ANALYTICS_ENDPOINT=your_endpoint_here
```

## Project Structure

```
├── src/                    # Source code
│   ├── utils/             # Utility modules
│   └── processors/        # Processing modules
├── output/                # Default output directory
├── config/                # Configuration files
└── examples/              # Example scripts
```

## Development

### Running Tests
```bash
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses `nodriver` for browser automation
- Powered by Azure Cognitive Services
- FFmpeg for media processing

## Troubleshooting

### Common Issues

1. **Browser not found**: Ensure Chrome/Chromium is installed
2. **FFmpeg not found**: Install FFmpeg and add to PATH
3. **Azure authentication fails**: Check your API keys in .env
4. **Download fails**: Verify the URL and password are correct

### Debug Mode

Enable debug logging:
```bash
export DEBUG=1  # On Windows: set DEBUG=1
python src/zoom_capture_download.py --url "..." --password "..." --debug
```

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/drdedge/zoom-webcast-downloader/issues) page.