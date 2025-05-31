# Zoom Recording Processor – Complete Solution

**Zoom Recording Processor** is a production‑ready Python application that automates the download of Zoom recordings and converts them into fully‑formatted artefacts: transcripts, AI summaries, presentation decks and Word reports. The codebase is designed for reliability in unattended, head‑less environments and can be integrated into larger data‑engineering workflows.

---

## 1  What the application does

When provided with a Zoom recording URL (or a local MP4), the program:

1. Establishes an authenticated browser session, navigates to the recording and retrieves the MP4 asset—even when the link is password‑protected or requires cookie consent. Robust retry logic keeps the process alive on flaky networks.
2. Splits the download into audio and video components. Audio is streamed into Azure Speech Services for diarised transcription; key video frames are detected by histogram analysis and saved for possible slide reconstruction.
3. Feeds the transcript to Azure OpenAI. A configurable prompt produces a structured summary that emphasises metrics, decisions and action items; you may substitute any deployed GPT‑compatible model.
4. Assembles the outputs—raw JSON from Speech Services, clean text, optional PowerPoint, summary text and a fully‑styled Word document—and places them in a versioned directory tree.

Because every function is exposed as a standalone class, you can execute the end‑to‑end pipeline, or call the downloader, transcription engine or document generator in isolation.

---

## 2  Key implementation details

* **Browser automation**: Selenium drives a Chromium instance in headless or headed mode. Authentication cookies are stored locally so subsequent downloads skip the login step.
* **Media handling**: FFmpeg (via `moviepy`) extracts audio to 48 kHz mono WAV; key‑frame detection uses OpenCV with an adjustable pixel‑difference threshold. Frame sequences can be exported directly to PowerPoint.
* **Resilience**: Each network or file operation is wrapped in an exponential‑back‑off retry decorator. Progress bars are streamed to the console with `tqdm` so long downloads remain visible.
* **Configuration hierarchy**: Settings can be supplied on the command line, in `.env`, as process environment variables or via a JSON config file. Precedence is command line > environment > JSON > defaults.
* **Logging**: The `logger_setup` utility initialises a rotating file handler plus a colourised console stream. Verbosity is adjustable with `--debug`.

---

## 3  Repository layout

```text
zoom-recording-processor/
├── zoom_capture_download_v2.py      # Zoom recording capture & download
├── mp4_processor.py                 # Media processing entry‑point
├── zoom_mp4_pipeline.py             # High‑level orchestrator
├── utils/                           # Support modules (config, media, AI, docs…)
├── output/                          # Default artefact tree (input / frames / outputs)
└── logs/                            # Rotating application logs
```

Each top‑level script exposes a CLI built with `typer`. Run `<script> --help` for option details.

---

## 4  Installation

1. **Clone and install dependencies**

   ```bash
   git clone https://github.com/<your‑org>/zoom-recording-processor.git
   cd zoom-recording-processor
   pip install -r requirements.txt
   ```

2. **Provision Azure resources**: create a Speech Services instance and an OpenAI deployment, then note the endpoint URLs and keys.

3. **Populate credentials**: copy `.env.template` to `.env` and insert the Azure keys, or export them as environment variables. Optionally generate `config.json` with `mp4_processor.py create-template`.

---

## 5  Typical command sequence

```bash
# Download and process in one step
python zoom_mp4_pipeline.py download-and-process \
  --url "https://zoom.us/rec/share/..." \
  --password "p@ssw0rd" \
  --process

# Process an existing MP4
python mp4_processor.py process \
  --mp4-path ./meeting.mp4 \
  --with-frames          # override default to save key frames
```

The first command authenticates to Zoom, downloads the video, triggers transcription and summary generation, and writes artefacts to `output/YYYY-MM-DD_HHMMSS/`.

---

## 6  Python API

Every CLI action maps to a callable. For example:

```python
from zoom_mp4_pipeline import full_pipeline

results = full_pipeline(
    zoom_url="https://zoom.us/rec/share/...",
    zoom_password="p@ssw0rd",
    config_file="config.json",
    output_dir="output"
)
print(results["transcript_txt"])
```

The returned dictionary contains absolute paths to the generated files as well as in‑memory objects where applicable.

---

## 7  Troubleshooting and FAQ

* **Missing Azure variables** – the application aborts with a clear message if any credential is absent. Run with `create-template` to list mandatory fields.
* **Download hangs at 99 %** – Increase `--timeout`; some large recordings require > 120 seconds to assemble on the Zoom CDN.
* **Speech API 300 MB limit** – pass `--no-transcribe` to skip the transcription stage and process the audio separately in chunks.

For verbose output add `--debug`; logs are routed to `logs/zoom_processor.log`.

---
