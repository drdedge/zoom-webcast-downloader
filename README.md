# Zoom Recording Processor

Transform recorded meetings into fully‑formatted, searchable documents in minutes.

In today’s information‑dense workplace, professionals are routinely sent links to Zoom calls, earnings presentations and webinars—often without transcripts or slide decks. Reviewing a single hour‑long recording can consume several hours of rewinds, screenshots and manual note‑taking. **Zoom Recording Processor** automates that workflow, turning each video into a polished Word document that captures both spoken content and visual material.

## How it works

Given a Zoom recording URL (including password‑protected links) or a local MP4 file, the pipeline:

1. Downloads the video
2. Extracts audio and detects significant presentation frames
3. Transcribes the conversation with Azure Speech Services, complete with speaker identification
4. Generates an executive‑style summary via Azure OpenAI, focusing on business metrics and decisions (the *o3‑mini* model performs especially well)
5. Compiles everything into a single, professional Word document

## Deliverables

* **Word document** containing meeting metadata, an executive summary, a full timestamped transcript with speaker labels, and any slides automatically inserted at the correct points
* **Searchable transcript** available as a standalone text file
* **AI summary** surfacing key performance indicators, strategic decisions and action items

## Why it matters

Investment analysts can process earnings calls or investor presentations moments after they finish, with every metric instantly searchable. Internal teams benefit from consistent, shareable records; hours previously spent drafting notes can be redirected to deeper analysis, and an archive of processed calls grows organically over time.

## Extensibility roadmap

Although the current release focuses on Zoom and generic MP4 uploads, the architecture is platform‑agnostic. Planned extensions include support for Viavid, Lumi and Cisco Webex streams.

## Recording tips

When a download link is unavailable—or when you wish to capture a live session—Windows Snipping Tool (`Win + Shift + S`) can record both screen and audio. A pixel‑sized selection suffices for audio‑only workflows, while a full‑frame selection preserves visuals for slide extraction. The tool functions well on virtual desktops, though it is not yet accessible from the command line.

## Custom summaries

The summarisation prompt is exposed in the configuration file, so you can tailor tone and focus to your own needs. Adjusting the prompt or model choice (for example, swapping *o3‑mini* for a domain‑specific model) changes the emphasis without altering the underlying pipeline.

---

All source code and setup instructions live in this repository. If you encounter issues or have suggestions, please open an issue—pull requests are very welcome.
