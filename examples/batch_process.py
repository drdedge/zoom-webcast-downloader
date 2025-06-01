#!/usr/bin/env python3
"""
Batch Processing Example
========================

This example shows how to process multiple recordings efficiently.
Supports processing from:
- CSV file with URLs and passwords
- Directory of MP4 files
- Text file with URLs

Usage:
    # Process from CSV
    python examples/batch_process.py --input-csv recordings.csv
    
    # Process directory of MP4s
    python examples/batch_process.py --input-dir ./recordings/
    
    # Process with parallel workers
    python examples/batch_process.py --input-csv recordings.csv --workers 3
"""

import sys
import os
from pathlib import Path
import csv
import concurrent.futures
from typing import List, Dict, Tuple
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from tqdm import tqdm
from src.mp4_processor import MP4Processor
from src.zoom_capture_download import download_recording
from src.utils.config_manager import ConfigManager
from src.utils.logger_setup import setup_logger


logger = setup_logger(name="batch_processor")


def process_single_recording(
    item: Dict,
    config: ConfigManager,
    output_base_dir: str,
    skip_download: bool = False
) -> Dict:
    """Process a single recording."""
    
    result = {
        'url': item.get('url', ''),
        'mp4_path': item.get('mp4_path', ''),
        'status': 'pending',
        'output_dir': None,
        'error': None,
        'start_time': datetime.now().isoformat()
    }
    
    try:
        # Create unique output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if item.get('name'):
            output_dir = os.path.join(output_base_dir, f"{item['name']}_{timestamp}")
        else:
            output_dir = os.path.join(output_base_dir, timestamp)
        
        os.makedirs(output_dir, exist_ok=True)
        result['output_dir'] = output_dir
        
        # Download if URL provided
        if item.get('url') and not skip_download:
            logger.info(f"Downloading: {item['url']}")
            mp4_path = download_recording(
                url=item['url'],
                password=item.get('password'),
                output_dir=output_dir,
                config=config
            )
            result['mp4_path'] = str(mp4_path)
        else:
            mp4_path = Path(item['mp4_path'])
        
        # Process the MP4
        logger.info(f"Processing: {mp4_path}")
        processor = MP4Processor(
            azure_config=config.azure.to_dict(),
            log_to_file=config.log_to_file,
            log_dir=config.log_dir
        )
        
        process_results = processor.process_video(
            mp4_path=str(mp4_path),
            output_dir=output_dir,
            extract_frames=config.processing.extract_frames,
            create_ppt=config.processing.create_ppt,
            transcribe=config.processing.transcribe,
            generate_summary=config.processing.generate_summary
        )
        
        result['status'] = 'completed'
        result['outputs'] = {
            'transcript': process_results.get('transcript_txt'),
            'summary': process_results.get('summary_txt'),
            'document': process_results.get('document_docx')
        }
        
    except Exception as e:
        logger.error(f"Failed to process {item}: {str(e)}")
        result['status'] = 'failed'
        result['error'] = str(e)
    
    result['end_time'] = datetime.now().isoformat()
    return result


def load_recordings_from_csv(csv_path: str) -> List[Dict]:
    """Load recording info from CSV file.
    
    Expected CSV format:
    url,password,name
    https://zoom.us/rec/share/...,p@ssw0rd,Meeting Name
    """
    recordings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recordings.append({
                'url': row.get('url', ''),
                'password': row.get('password', ''),
                'name': row.get('name', '')
            })
    return recordings


def load_recordings_from_directory(dir_path: str) -> List[Dict]:
    """Load MP4 files from directory."""
    recordings = []
    path = Path(dir_path)
    
    for mp4_file in path.glob("*.mp4"):
        recordings.append({
            'mp4_path': str(mp4_file),
            'name': mp4_file.stem
        })
    
    return recordings


@click.command()
@click.option('--input-csv', help='CSV file with recording URLs and passwords')
@click.option('--input-dir', help='Directory containing MP4 files')
@click.option('--output-dir', default='batch_output', help='Base output directory')
@click.option('--config-file', default='config.json', help='Configuration file')
@click.option('--workers', default=1, help='Number of parallel workers')
@click.option('--skip-download', is_flag=True, help='Skip download phase (for MP4s)')
@click.option('--report', default='batch_report.json', help='Report file path')
def main(
    input_csv: str,
    input_dir: str,
    output_dir: str,
    config_file: str,
    workers: int,
    skip_download: bool,
    report: str
):
    """Batch process multiple recordings."""
    
    if not input_csv and not input_dir:
        click.echo("❌ Please provide either --input-csv or --input-dir")
        return
    
    # Load configuration
    config = ConfigManager.from_file(config_file)
    
    # Load recordings
    if input_csv:
        recordings = load_recordings_from_csv(input_csv)
        print(f"📋 Loaded {len(recordings)} recordings from CSV")
    else:
        recordings = load_recordings_from_directory(input_dir)
        print(f"📁 Found {len(recordings)} MP4 files")
    
    if not recordings:
        print("❌ No recordings found to process")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process recordings
    results = []
    print(f"\n🔄 Processing {len(recordings)} recordings with {workers} workers...")
    
    if workers > 1:
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            futures = []
            for recording in recordings:
                future = executor.submit(
                    process_single_recording,
                    recording,
                    config,
                    output_dir,
                    skip_download
                )
                futures.append(future)
            
            # Process results with progress bar
            with tqdm(total=len(recordings)) as pbar:
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
                    pbar.update(1)
                    
                    # Update progress bar description
                    status = "✅" if result['status'] == 'completed' else "❌"
                    pbar.set_description(f"{status} Last: {result.get('url', result.get('mp4_path', ''))[:50]}...")
    else:
        # Sequential processing
        for recording in tqdm(recordings):
            result = process_single_recording(
                recording,
                config,
                output_dir,
                skip_download
            )
            results.append(result)
    
    # Generate report
    completed = sum(1 for r in results if r['status'] == 'completed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\n📊 Batch Processing Complete!")
    print(f"✅ Completed: {completed}")
    print(f"❌ Failed: {failed}")
    
    # Save detailed report
    with open(report, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': len(recordings),
                'completed': completed,
                'failed': failed,
                'timestamp': datetime.now().isoformat()
            },
            'results': results
        }, f, indent=2)
    
    print(f"📄 Detailed report saved to: {report}")
    
    # Print failures
    if failed > 0:
        print("\n❌ Failed recordings:")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - {r.get('url', r.get('mp4_path'))}: {r['error']}")


if __name__ == "__main__":
    main()