# Zoom Recording Processor

Transform recorded meetings into fully‑formatted, searchable documents in minutes.

In today's information‑dense workplace, professionals are routinely sent links to Zoom calls, earnings presentations and webinars—often without transcripts or slide decks. Reviewing a single hour‑long recording can consume several hours of rewinds, screenshots and manual note‑taking. **Zoom Recording Processor** automates that workflow, turning each video into a polished Word document that captures both spoken content and visual material.

## How it works

Given a Zoom recording URL (including password‑protected links) or a local MP4 file, the pipeline:

1. Downloads the video using advanced browser automation that handles authentication and passwords
2. Extracts audio and intelligently detects significant presentation frames
3. Transcribes the conversation with Azure Speech Services, complete with speaker identification
4. Generates an executive‑style summary via Azure OpenAI, focusing on business metrics and decisions (the *o3‑mini* model performs especially well)
5. Compiles everything into a single, professional Word document with embedded slides

## Deliverables

* **Word document** containing meeting metadata, an executive summary, a full timestamped transcript with speaker labels, and any slides automatically inserted at the correct points
* **Searchable transcript** available as a standalone text file
* **AI summary** surfacing key performance indicators, strategic decisions and action items

## Why it matters

Investment analysts can process earnings calls or investor presentations moments after they finish, with every metric instantly searchable. Internal teams benefit from consistent, shareable records; hours previously spent drafting notes can be redirected to deeper analysis, and an archive of processed calls grows organically over time.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/zoom-webcast-downloader.git
cd zoom-webcast-downloader

# Install dependencies
pip install -r requirements.txt

```

FFmpeg is required for audio and video processing. Windows users can install it with `choco install ffmpeg` (ensure Chocolatey is installed first). Linux users can run `sudo apt-get install ffmpeg`, and macOS users can `brew install ffmpeg`.

```bash
# Copy and configure settings
cp config.json.template config.json
# Edit config.json with your Azure credentials

# Process a Zoom recording
python src/zoom_capture_download.py --url "https://zoom.us/rec/share/..." --password "p@ssw0rd"
python src/mp4_processor.py process --mp4-path ./output/downloaded.mp4
```

See the [examples](examples/) directory for more usage patterns.

## Extensibility roadmap

Although the current release focuses on Zoom and generic MP4 uploads, the architecture is platform‑agnostic. Planned extensions include support for Viavid, Lumi and Cisco Webex streams.

## Recording tips

When a download link is unavailable—or when you wish to capture a live session—Windows Snipping Tool (`Win + Shift + S`) can record both screen and audio. A pixel‑sized selection suffices for audio‑only workflows, while a full‑frame selection preserves visuals for slide extraction. The tool functions well on virtual desktops, though it is not yet accessible from the command line.

## Custom summaries

The summarisation prompt is now modular and exposed in `src/utils/mp4_processing/prompts.py`, so you can tailor tone and focus to your own needs. Adjusting the prompt or model choice (for example, swapping *o3‑mini* for a domain‑specific model) changes the emphasis without altering the underlying pipeline.

---
## Advanced Extension Possibilities

This tool has been built as a standalone module that can sit in a broader solution to avoid vendor lock-in. Each component can be extended independently or integrated into broader data platforms. There are a number of extensions that are relatively straightforward to add depending on the target outputs:

### OCR-Enhanced Slide Analysis
Beyond basic frame extraction, OCR capabilities can parse text and numerical data directly from presentation slides. This enables automatic extraction of:
- Financial metrics displayed in charts and tables
- Key performance indicators from dashboard screenshots  
- Text-heavy slides that current frame detection might miss

### Intelligent Financial Data Extraction
Purpose-built LLM prompts can identify and structure critical business metrics:
- Automatically extract revenue figures, growth rates, and guidance
- Tag discussions of M&A activity, debt structures, or capital allocation
- Generate structured JSON outputs for downstream analytics systems

This can often be complementary to published materials (for example SEC filings), where the additional commentary and non-statutory figures are outlined in Investor calls.

### Enterprise UI Integration
While the CLI serves technical users well, non-technical stakeholders benefit from web interfaces. A proven pattern:
- Web form submissions write to SQL database
- Airflow DAGs monitor for new entries and trigger processing
- Doc processor uses a semi-formatted DOCX template to maintain corporate branding
- SendGrid delivers formatted documents to specified recipients

This approach maintains the tool's modularity while enabling self-service access.

### Multi-Provider LLM Support
The recent refactoring introduces a modular LLM client architecture:
- `azure_client.py` handles Azure OpenAI endpoints
- Easy to add `openai_client.py`, `anthropic_client.py`, etc.
- All clients use litellm for consistent interface
- Switch providers without changing core logic

### Live Capture Considerations
This tool is not intended to provide "live transcription" where existing services such as Copilot and Otter.ai already handle real-time transcription. The tool is aimed to address a gap where a transcript is not available/somewhat delayed, and this enables immediate generation and output for business users.

Windows Snipping Tool already enables immediate post-meeting capture, providing a pragmatic middle ground in cases where "near live" is needed.

### Platform Integration Philosophy
The tool's modular design reflects hard-won lessons about vendor lock-in and integration friction. By exposing each capability as a standalone class:
- Calendar systems can trigger automatic processing of recurring calls
- Outputs flow directly to data warehouses or document management systems  
- Authentication and storage remain under your control

---
## Technical Documentation

For detailed technical documentation, architecture diagrams, and API reference, see the [src/README.md](src/README.md).

---
All source code and setup instructions live in this repository. If you encounter issues or have suggestions, please open an issue—pull requests are very welcome.