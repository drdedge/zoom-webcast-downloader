#!/usr/bin/env python3
"""
Custom Prompts Example
======================

This example demonstrates how to use different prompts from the prompts.py module
for specialized summaries.

The prompts.py module contains templates for:
- General meeting summaries
- Earnings calls
- Board meetings  
- Technical demos
- Sales presentations

Usage:
    python examples/custom_prompts.py --mp4-path meeting.mp4 --prompt-type earnings
    python examples/custom_prompts.py --mp4-path demo.mp4 --prompt-type technical
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from src.utils.mp4_processing.ai_processing import AIProcessor
from src.utils.mp4_processing.media_processing import MediaProcessor
from src.utils.mp4_processing.prompts import PROMPTS
from src.utils.config_manager import ConfigManager


def process_with_prompt_type(
    mp4_path: str,
    prompt_type: str,
    config: ConfigManager,
    output_dir: str = None
) -> dict:
    """Process an MP4 with a specific prompt type from prompts.py."""
    
    mp4_path = Path(mp4_path)
    if not mp4_path.exists():
        raise FileNotFoundError(f"MP4 file not found: {mp4_path}")
    
    # Get the prompt template
    if prompt_type not in PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}. Available: {list(PROMPTS.keys())}")
    
    prompt_template = PROMPTS[prompt_type]
    
    # Set up output directory
    if not output_dir:
        output_dir = f"output/{prompt_type}_{mp4_path.stem}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize processors
    media_processor = MediaProcessor()
    ai_processor = AIProcessor(
        speech_key=config.azure.speech_key,
        speech_endpoint=config.azure.speech_endpoint,
        azure_endpoint=config.azure.openai_endpoint,
        model_name=config.azure.model_name,
        api_key=config.azure.openai_key,
        api_version=config.azure.api_version
    )
    
    results = {}
    
    # Extract audio
    print("🎵 Extracting audio...")
    audio_path = Path(output_dir) / "audio.wav"
    media_processor.extract_audio(mp4_path, audio_path)
    results['audio'] = str(audio_path)
    
    # Transcribe
    print("📝 Transcribing audio...")
    transcript_json = ai_processor.transcribe_audio(audio_path)
    
    if transcript_json:
        # Save raw transcript
        transcript_json_path = Path(output_dir) / "transcript.json"
        with open(transcript_json_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(transcript_json, f, indent=2)
        
        # Process to text
        transcript_text = ai_processor.process_transcript(transcript_json)
        transcript_txt_path = Path(output_dir) / "transcript.txt"
        with open(transcript_txt_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        results['transcript'] = str(transcript_txt_path)
        
        # Generate summary with selected prompt
        print(f"🤖 Generating {prompt_type} summary...")
        prompt = prompt_template.format(transcript=transcript_text)
        summary = ai_processor.ask_llm(prompt, max_completion_tokens=3000)
        
        if summary:
            summary_path = Path(output_dir) / f"{prompt_type}_summary.md"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"# {prompt_type.title()} Summary\n\n")
                f.write(summary)
            results['summary'] = str(summary_path)
            
            print(f"\n✅ {prompt_type.title()} summary saved to: {summary_path}")
            print("\n--- Summary Preview ---")
            print(summary[:500] + "..." if len(summary) > 500 else summary)
    
    return results


@click.command()
@click.option('--mp4-path', required=True, help='Path to MP4 file')
@click.option('--prompt-type', 
              type=click.Choice(['meeting', 'earnings', 'board', 'technical', 'sales']),
              default='meeting',
              help='Type of summary to generate')
@click.option('--output-dir', help='Output directory')
@click.option('--config-file', default='config.json', help='Configuration file')
@click.option('--list-prompts', is_flag=True, help='List available prompt types')
def main(mp4_path: str, prompt_type: str, output_dir: str, config_file: str, list_prompts: bool):
    """Process MP4 with specialized prompts from prompts.py module."""
    
    if list_prompts:
        print("📋 Available prompt types in prompts.py:")
        for name, prompt in PROMPTS.items():
            # Extract first line of prompt description
            first_line = prompt.strip().split('\n')[1] if '\n' in prompt else name
            print(f"  - {name}: {first_line}")
        print("\nTo add new prompts, edit src/utils/mp4_processing/prompts.py")
        return
    
    # Load configuration
    config = ConfigManager.from_file(config_file)
    
    print(f"📋 Using '{prompt_type}' prompt template")
    
    # Process with selected prompt
    try:
        results = process_with_prompt_type(
            mp4_path=mp4_path,
            prompt_type=prompt_type,
            config=config.azure,
            output_dir=output_dir
        )
        
        print(f"\n✅ Processing complete!")
        print(f"📁 Output directory: {output_dir or f'output/{prompt_type}_{Path(mp4_path).stem}'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()