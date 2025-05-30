#!/usr/bin/env python3
"""
MP4 File Processor (Production Ready)
=====================================

A modular pipeline that processes MP4 videos with the following workflow:
1. Directory setup and file validation
2. Audio extraction to MP3
3. Frame extraction for scene changes
4. PowerPoint generation from frames
5. Audio transcription via Azure Speech API
6. AI-powered meeting summary generation
7. Combined Word document creation

Usage:
    python mp4_processor.py
"""

import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import click

# Import utilities
from utils.logger_setup import setup_logger
from utils.media_processing import MediaProcessor
from utils.ai_processing import AIProcessor
from utils.document_generation import DocumentGenerator
from utils.word_formatter import WordDocFormatter
from utils.config_manager import ConfigManager


class MP4Processor:
    """Main processor class that orchestrates the MP4 processing pipeline."""
    
    def __init__(self, 
                 azure_config: dict,
                 log_to_file: bool = True,
                 log_dir: str = "logs"):
        """
        Initialize the MP4 processor.
        
        Args:
            azure_config: Dictionary with Azure configuration
            log_to_file: Whether to log to file
            log_dir: Directory for log files
        """
        self.logger = setup_logger()
        
        # Initialize processors
        self.media_processor = MediaProcessor()
        self.ai_processor = AIProcessor(
            speech_key=azure_config['speech_key'],
            speech_endpoint=azure_config['speech_endpoint'],
            azure_endpoint=azure_config['azure_endpoint'],
            model_name=azure_config['model_name'],
            api_key=azure_config['api_key'],
            api_version=azure_config.get('api_version', '2024-02-15-preview')
        )
        self.doc_generator = DocumentGenerator()
        self.word_formatter = WordDocFormatter()
    
    def process_mp4(self, 
                   mp4_path: str, 
                   output_dir: str,
                   extract_frames: bool = True,
                   create_ppt: bool = True,
                   transcribe: bool = True,
                   generate_summary: bool = True) -> Dict[str, Path]:
        """
        Run the complete MP4 processing pipeline.
        
        Args:
            mp4_path: Path to input MP4 file
            output_dir: Base output directory
            extract_frames: Whether to extract video frames
            create_ppt: Whether to create PowerPoint from frames
            transcribe: Whether to transcribe audio
            generate_summary: Whether to generate AI summary
            
        Returns:
            Dictionary of output file paths
        """
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Starting MP4 processing pipeline")
        self.logger.info(f"Input: {mp4_path}")
        self.logger.info(f"Output: {output_dir}")
        self.logger.info(f"{'='*60}")
        
        mp4_path_obj = Path(mp4_path).expanduser().resolve()
        
        # Validate input file
        if not mp4_path_obj.exists():
            raise FileNotFoundError(f"Input file not found: {mp4_path}")
        
        # Create output directories
        dirs = self.doc_generator.create_output_structure(
            output_dir, 
            ["input", "frame_images", "outputs"]
        )
        
        # Copy input file
        input_copy = dirs["input"] / mp4_path_obj.name
        shutil.copy2(mp4_path_obj, input_copy)
        self.logger.info(f"Input file copied. Size: {input_copy.stat().st_size / (1024*1024):.2f} MB")
        
        # Validate media file
        validation = self.media_processor.validate_media_file(input_copy)
        if not validation['valid']:
            errors = "\n".join(validation['errors'])
            raise ValueError(f"Media validation failed:\n{errors}")
        
        self.logger.info(f"Media validation passed. Duration: {validation['duration_hours']:.2f} hours")
        
        # Extract audio
        mp3_path = dirs["outputs"] / (mp4_path_obj.stem + ".mp3")
        if not self.media_processor.extract_audio(input_copy, mp3_path):
            raise RuntimeError("Audio extraction failed")
        
        results = {
            "input_copy": input_copy,
            "audio_mp3": mp3_path,
        }
        
        # Extract frames (optional)
        if extract_frames:
            frame_count = self.media_processor.extract_changed_frames(
                input_copy, 
                dirs["frame_images"]
            )
            results["frames_dir"] = dirs["frame_images"]
            results["frame_count"] = frame_count
            
            # Create PowerPoint (optional)
            if create_ppt and frame_count > 0:
                ppt_path = dirs["outputs"] / (mp4_path_obj.stem + "_frames.pptx")
                if self.doc_generator.create_ppt_from_frames(dirs["frame_images"], ppt_path):
                    results["pptx"] = ppt_path
        
        # Transcribe audio (optional)
        transcript_text = ""
        if transcribe:
            # Validate audio file for transcription
            audio_validation = self.media_processor.validate_media_file(
                mp3_path,
                max_size_mb=300,
                max_duration_hours=2
            )
            
            if not audio_validation['valid']:
                self.logger.warning(f"Audio file validation failed for transcription: {audio_validation['errors']}")
            else:
                transcript_json = self.ai_processor.transcribe_audio(mp3_path)
                
                if transcript_json:
                    # Save JSON
                    transcript_json_path = dirs["outputs"] / (mp4_path_obj.stem + "_transcript.json")
                    with transcript_json_path.open("w", encoding="utf-8") as f:
                        json.dump(transcript_json, f, indent=2)
                    results["transcript_json"] = transcript_json_path
                    
                    # Process transcript
                    transcript_text = self.ai_processor.process_transcript(transcript_json)
                    transcript_path = dirs["outputs"] / (mp4_path_obj.stem + "_transcript.txt")
                    with transcript_path.open("w", encoding="utf-8") as f:
                        f.write(transcript_text)
                    results["transcript_txt"] = transcript_path
                else:
                    self.logger.error("Transcription failed")
        
        # Generate summary (optional)
        summary_text = ""
        if generate_summary and transcript_text:
            summary_text = self.ai_processor.generate_meeting_summary(transcript_text)
            summary_path = dirs["outputs"] / (mp4_path_obj.stem + "_summary.txt")
            with summary_path.open("w", encoding="utf-8") as f:
                f.write(summary_text)
            results["summary_txt"] = summary_path
        
        # Get video duration
        duration_seconds = self.media_processor.get_video_duration(input_copy)
        duration_td = timedelta(seconds=int(duration_seconds)) if duration_seconds else timedelta(0)
        
        # Build combined document
        if transcript_text or summary_text:
            markdown = self.doc_generator.build_markdown_document(
                title=mp4_path_obj.name,
                created=datetime.now(),
                duration=duration_td,
                summary=summary_text or "No summary generated",
                transcript=transcript_text or "No transcript available",
                additional_metadata={
                    "File Size": f"{validation['size_mb']:.1f} MB",
                    "Frame Count": results.get("frame_count", "N/A")
                }
            )
            
            docx_path = dirs["outputs"] / (mp4_path_obj.stem + ".docx")
            if self.word_formatter.markdown_to_docx(markdown, output_filepath=str(docx_path)):
                results["docx"] = docx_path
        
        self.logger.info(f"{'='*60}")
        self.logger.info("Processing completed successfully!")
        self.logger.info(f"Output files saved to: {dirs['outputs']}")
        self.logger.info(f"{'='*60}")
        
        return results


@click.command()
@click.option('--mp4-path', '-i', required=True, help='Path to input MP4 file')
@click.option('--output-dir', '-o', help='Output directory (overrides config)')
@click.option('--config', '-c', help='Configuration file path')
@click.option('--no-frames', is_flag=True, help='Skip frame extraction')
@click.option('--no-ppt', is_flag=True, help='Skip PowerPoint creation')
@click.option('--no-transcribe', is_flag=True, help='Skip transcription')
@click.option('--no-summary', is_flag=True, help='Skip summary generation')
@click.option('--no-log-file', is_flag=True, help='Disable file logging')
@click.option('--save-config', is_flag=True, help='Save current configuration')
def main(mp4_path, output_dir, config, no_frames, no_ppt, no_transcribe, 
         no_summary, no_log_file, save_config):
    """
    Process MP4 files with transcription and AI summarization.
    
    Configuration is loaded from (in order of precedence):
    1. Command line arguments
    2. Environment variables (AZURE_SPEECH_KEY, etc.)
    3. Configuration file (--config or default locations)
    4. Default values
    """
    
    # Load configuration
    config_mgr = ConfigManager(config_file=config)
    
    # Override with command line arguments
    config_mgr.override_with_args(
        output_dir=output_dir,
        extract_frames=not no_frames,
        create_ppt=not no_ppt,
        transcribe=not no_transcribe,
        generate_summary=not no_summary,
        log_to_file=not no_log_file
    )
    
    # Validate configuration
    if not config_mgr.validate():
        click.echo("❌ Azure configuration is incomplete!", err=True)
        click.echo("\nRequired settings:")
        click.echo("  - AZURE_SPEECH_KEY")
        click.echo("  - AZURE_SPEECH_ENDPOINT")
        click.echo("  - AZURE_OPENAI_ENDPOINT")
        click.echo("  - AZURE_OPENAI_KEY")
        click.echo("\nSet via environment variables or configuration file.")
        click.echo("\nCreate a template with: python mp4_processor.py --create-template")
        raise click.Abort()
    
    # Save configuration if requested
    if save_config:
        config_mgr.save_to_file()
        click.echo(f"✅ Configuration saved to: {config_mgr.config_file or 'config.json'}")
    
    # Initialize processor
    processor = MP4Processor(
        azure_config=config_mgr.get_azure_config(),
        log_to_file=config_mgr.config.log_to_file,
        log_dir=config_mgr.config.log_dir
    )
    
    try:
        # Process MP4
        results = processor.process_mp4(
            mp4_path=mp4_path,
            output_dir=config_mgr.config.output_dir,
            extract_frames=config_mgr.config.processing.extract_frames,
            create_ppt=config_mgr.config.processing.create_ppt,
            transcribe=config_mgr.config.processing.transcribe,
            generate_summary=config_mgr.config.processing.generate_summary
        )
        
        # Print results
        click.echo("\nProcessing completed! Output files:")
        for key, path in results.items():
            if isinstance(path, Path) and path.exists():
                click.echo(f"  - {key}: {path}")
                
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort()


@click.command()
def create_template():
    """Create a configuration template file."""
    config_mgr = ConfigManager()
    config_mgr.create_template()


# Create CLI group
@click.group()
def cli():
    """MP4 Processor - Process videos with AI transcription and summarization."""
    pass

cli.add_command(main, name='process')
cli.add_command(create_template, name='create-template')


if __name__ == "__main__":
    cli()