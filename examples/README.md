# Zoom Recording Processor - Examples

This directory contains practical examples demonstrating how to use the Zoom Recording Processor in various scenarios.

## Example Scripts

### 1. Basic Usage (`basic_usage.py`)
Simple example showing how to download and process a Zoom recording.

### 2. Batch Processing (`batch_process.py`)
Process multiple recordings from a CSV file or directory.

### 3. Custom Prompts (`custom_prompts.py`)
Examples of using different prompts for specialized summaries (earnings calls, board meetings, etc.).

### 4. API Integration (`api_integration.py`)
Using the Python API directly for integration with other systems.

### 5. Enterprise Pipeline (`enterprise_pipeline.py`)
Advanced example showing integration with databases, email notifications, and scheduled processing.

### 6. Custom LLM Provider (`custom_llm_provider.py`)
Example of adding support for a new LLM provider (OpenAI, Anthropic, etc.).

## Quick Start

1. Copy `config.json.template` to `config.json` and add your Azure credentials
2. Run any example script:
   ```bash
   python examples/basic_usage.py
   ```

## Environment Setup

Make sure you have:
- Python 3.8+
- All requirements installed: `pip install -r requirements.txt`
- Azure credentials configured in `config.json` or environment variables
- FFmpeg installed for media processing

## Common Use Cases

### Processing a Single Recording
```bash
python examples/basic_usage.py --url "https://zoom.us/rec/share/..." --password "pass"
```

### Batch Processing Multiple Files
```bash
python examples/batch_process.py --input-csv recordings.csv --output-dir results/
```

### Custom Summary for Earnings Call
```bash
python examples/custom_prompts.py --mp4-path earnings_call.mp4 --prompt-type earnings
```

## Tips

- Use `--debug` flag for detailed logging
- Check `logs/` directory for troubleshooting
- Customize prompts in `src/utils/mp4_processing/prompts.py`
- See `src/README.md` for technical documentation