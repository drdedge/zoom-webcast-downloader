#!/usr/bin/env python3
"""
Basic Usage Example
===================

This example demonstrates the simplest way to use the Zoom Recording Processor
to download and process a Zoom recording.

Usage:
    python examples/basic_usage.py --url "https://zoom.us/rec/share/..." --password "p@ssw0rd"
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from src.zoom_capture_download import main as download_zoom
from src.mp4_processor import MP4Processor
from src.utils.config_manager import ConfigManager


@click.command()
@click.option('--url', required=True, help='Zoom recording URL')
@click.option('--password', default=None, help='Recording password if required')
@click.option('--config-file', default='config.json', help='Path to config file')
@click.option('--output-dir', default='output', help='Output directory')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(url: str, password: str, config_file: str, output_dir: str, debug: bool):
    """Download and process a Zoom recording in one go."""
    
    print(f"🎬 Starting Zoom Recording Processor")
    print(f"📥 URL: {url}")
    
    # Load configuration
    config = ConfigManager.from_file(config_file)
    
    # Step 1: Download the recording
    print("\n📥 Downloading Zoom recording...")
    download_args = [
        '--url', url,
        '--output-dir', output_dir
    ]
    
    if password:
        download_args.extend(['--password', password])
    
    if debug:
        download_args.append('--debug')
    
    # Download the recording
    try:
        download_zoom(download_args)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return
    
    # Step 2: Find the downloaded MP4
    output_path = Path(output_dir)
    mp4_files = list(output_path.glob("*.mp4"))
    
    if not mp4_files:
        print("❌ No MP4 file found in output directory")
        return
    
    mp4_path = mp4_files[0]  # Use the first (most recent) MP4
    print(f"\n📹 Found MP4: {mp4_path.name}")
    
    # Step 3: Process the MP4
    print("\n🔄 Processing MP4 file...")
    processor = MP4Processor(
        azure_config=config.azure.to_dict(),
        log_to_file=config.log_to_file,
        log_dir=config.log_dir
    )
    
    try:
        results = processor.process_video(
            mp4_path=str(mp4_path),
            output_dir=output_dir,
            extract_frames=config.processing.extract_frames,
            create_ppt=config.processing.create_ppt,
            transcribe=config.processing.transcribe,
            generate_summary=config.processing.generate_summary
        )
        
        print("\n✅ Processing complete!")
        print(f"📁 Output directory: {results['output_dir']}")
        
        if results.get('transcript_txt'):
            print(f"📝 Transcript: {results['transcript_txt']}")
        
        if results.get('summary_txt'):
            print(f"📊 Summary: {results['summary_txt']}")
        
        if results.get('document_docx'):
            print(f"📄 Word Document: {results['document_docx']}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        if debug:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()