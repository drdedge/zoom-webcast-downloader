# utils/media_processing.py
"""
Media Processing Utilities
Handles audio/video extraction and frame processing
"""

from pathlib import Path
import logging
from typing import Optional, List
import cv2
import ffmpeg
import numpy as np

from ..logger_setup import setup_logger

logger = setup_logger(name="media_processor", level=logging.INFO)


class MediaProcessor:
    """Handles media file processing operations."""
    
    def __init__(self):
        self.logger = logger
    
    def extract_audio(self, input_path: Path, output_path: Path, fmt: str = "mp3") -> bool:
        """
        Extract audio from video file.
        
        Args:
            input_path: Path to input video file
            output_path: Path for output audio file
            fmt: Audio format ('mp3' or 'aac')
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Starting audio extraction from {input_path.name} to {output_path.name} in {fmt} format")
        try:
            stream = ffmpeg.input(str(input_path))
            if fmt == "mp3":
                stream = ffmpeg.output(stream, str(output_path), acodec="mp3", vn=None)
            else:
                stream = ffmpeg.output(stream, str(output_path), acodec="aac", vn=None)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            self.logger.info(f"Audio extraction completed successfully to {output_path}")
            return True
        except ffmpeg.Error as exc:
            err_msg = exc.stderr.decode() if hasattr(exc, "stderr") else str(exc)
            self.logger.error(f"Audio extraction failed: {err_msg}")
            return False
    
    def get_video_duration(self, video_path: Path) -> Optional[float]:
        """
        Get video duration in seconds.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds or None if error
        """
        try:
            meta = ffmpeg.probe(str(video_path))
            return float(meta["format"]["duration"])
        except Exception as err:
            self.logger.error(f"Could not read video duration: {err}")
            return None
    
    def extract_changed_frames(
        self,
        video_path: Path,
        frames_dir: Path,
        threshold: int = 30,
        log_interval: int = 10
    ) -> int:
        """
        Extract frames when scene changes significantly.
        
        Args:
            video_path: Path to video file
            frames_dir: Directory to save frames
            threshold: Mean absolute difference threshold for detecting changes
            log_interval: How often to log progress (every N frames)
            
        Returns:
            Number of frames extracted
        """
        self.logger.info(f"Starting frame extraction from {video_path.name} to {frames_dir}")
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        prev_gray: Optional[np.ndarray] = None
        saved = 0
        index = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            changed = (
                prev_gray is None
                or np.mean(cv2.absdiff(gray, prev_gray)) > threshold
            )
            
            if changed:
                # timestamp in whole seconds
                sec = int(index / fps)
                mm = sec // 60
                ss = sec % 60
                fname = f"frame_{mm:02d}{ss:02d}_{saved + 1:03d}.png"
                output_frame_path = frames_dir / fname
                cv2.imwrite(str(output_frame_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                saved += 1
                
                if saved % log_interval == 0:
                    self.logger.info(f"Saved frame {saved}: {fname}")

            prev_gray = gray
            index += 1

            if total and index % max(total // 10, 1) == 0:
                pct = (index / total) * 100
                self.logger.info(f"Frame extraction progress: {pct:.1f}% - {saved} frames saved")

        cap.release()
        self.logger.info(f"Frame extraction completed. Total frames extracted: {saved}")
        return saved
    
    def validate_media_file(self, file_path: Path, max_size_mb: float = 300, max_duration_hours: float = 2) -> dict:
        """
        Validate media file size and duration.
        
        Args:
            file_path: Path to media file
            max_size_mb: Maximum allowed size in MB
            max_duration_hours: Maximum allowed duration in hours
            
        Returns:
            Dict with validation results
        """
        result = {
            'valid': True,
            'size_mb': 0,
            'duration_hours': 0,
            'errors': []
        }
        
        # Check file size
        size_mb = file_path.stat().st_size / 1024 / 1024
        result['size_mb'] = size_mb
        
        if size_mb > max_size_mb:
            result['valid'] = False
            result['errors'].append(f"File size {size_mb:.1f} MB exceeds {max_size_mb} MB limit")
        
        # Check duration
        duration_seconds = self.get_video_duration(file_path)
        if duration_seconds:
            duration_hours = duration_seconds / 3600
            result['duration_hours'] = duration_hours
            
            if duration_hours > max_duration_hours:
                result['valid'] = False
                result['errors'].append(f"Duration {duration_hours:.2f} hours exceeds {max_duration_hours} hour limit")
        else:
            result['valid'] = False
            result['errors'].append("Could not determine file duration")
        
        return result