# utils/ai_processing.py
"""
AI and Transcription Processing Utilities
Handles speech-to-text, LLM interactions, and content generation
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union
import requests

from ..logger_setup import setup_logger
from .azure_client import AzureLLMClient
from .prompts import MEETING_SUMMARY_PROMPT

logger = setup_logger(name="config_manager", level=logging.INFO)



class AIProcessor:
    """Handles AI-related processing including transcription and LLM interactions."""
    
    def __init__(self, 
                 speech_key: str,
                 speech_endpoint: str,
                 azure_endpoint: str,
                 model_name: str,
                 api_key: str,
                 api_version: str = "2024-02-15-preview"):
        """
        Initialize AI processor with credentials.
        
        Args:
            speech_key: Azure Speech API key
            speech_endpoint: Azure Speech endpoint URL
            azure_endpoint: Azure OpenAI endpoint URL
            model_name: Model name (e.g., "azure/gpt-4")
            api_key: Azure OpenAI API key
            api_version: API version
        """
        self.speech_key = speech_key
        self.speech_endpoint = speech_endpoint
        self.logger = logger
        
        # Initialize Azure LLM client
        self.llm_client = AzureLLMClient(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            model_name=model_name,
            api_version=api_version
        )
    
    def ask_llm(self, prompt: str, max_completion_tokens: int = 10000) -> Optional[str]:
        """
        Send a prompt to Azure OpenAI via litellm.
        
        Args:
            prompt: The prompt to send
            max_completion_tokens: Maximum tokens in response
            
        Returns:
            LLM response or None if error
        """
        return self.llm_client.complete(
            prompt=prompt,
            max_completion_tokens=max_completion_tokens
        )
    
    def extract_codeblock(self, text: str, block_type: str = "markdown") -> Optional[str]:
        """
        Extract content from a code block.
        
        Args:
            text: Text containing the code block
            block_type: Type of code block (e.g., "markdown", "python")
            
        Returns:
            Content of the code block or None
        """
        try:
            pattern = rf"```{block_type}(.*?)```"
            match = re.search(pattern, text, re.DOTALL)
            
            if match:
                extracted_content = match.group(1).strip()
                self.logger.debug(f"Successfully extracted {block_type} block")
                return extracted_content
            
            self.logger.debug(f"No {block_type} block found in text")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting {block_type} block: {str(e)}")
            return None
    
    def transcribe_audio(
        self,
        audio_file: Union[str, Path],
        locales: List[str] = ["en-US"],
        profanity_mode: str = "Masked",
        diarization: bool = True,
        max_speakers: int = 10,
        api_version: str = "2024-11-15",
        timeout: int = 300,
    ) -> Optional[Dict]:
        """
        Transcribe audio file using Azure Speech-to-Text.
        
        Args:
            audio_file: Path to audio file
            locales: List of locales for transcription
            profanity_mode: How to handle profanity
            diarization: Whether to enable speaker diarization
            max_speakers: Maximum number of speakers to detect
            api_version: API version
            timeout: Request timeout in seconds
            
        Returns:
            Transcription JSON response or None if error
        """
        audio_path = Path(audio_file).expanduser().resolve()
        self.logger.info(f"Starting speech-to-text transcription for {audio_path.name}")
        
        url = f"{self.speech_endpoint}/speechtotext/transcriptions:transcribe?api-version={api_version}"
        
        definition = {
            "locales": locales,
            "profanityFilterMode": profanity_mode,
            "diarization": {"enabled": diarization, "maxSpeakers": max_speakers},
        }
        
        try:
            with audio_path.open("rb") as fh:
                files = {
                    "audio": (audio_path.name, fh, "audio/mpeg"),
                    "definition": (None, json.dumps(definition), "application/json"),
                }
                headers = {
                    "Ocp-Apim-Subscription-Key": self.speech_key,
                    "Accept": "application/json",
                }
                
                response = requests.post(url, headers=headers, files=files, timeout=timeout)
            
            response.raise_for_status()
            self.logger.info("Transcription completed successfully")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Transcription request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during transcription: {e}")
            return None
    
    def process_transcript(self, transcript_json: Dict) -> str:
        """
        Convert Azure Speech-to-Text JSON to formatted text.
        
        Args:
            transcript_json: JSON response from Azure Speech API
            
        Returns:
            Formatted transcript with timestamps and speaker labels
        """
        self.logger.info("Processing transcript JSON to formatted text")
        phrases: List[dict] = transcript_json.get("phrases", [])
        phrases.sort(key=lambda p: p.get("offsetMilliseconds", 0))

        lines: List[str] = []
        for p in phrases:
            offset_ms = p.get("offsetMilliseconds", 0)
            total_sec = offset_ms // 1000
            hours, rem_sec = divmod(total_sec, 3600)
            mins, secs = divmod(rem_sec, 60)
            
            timestamp = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours else f"{mins:02d}:{secs:02d}"
            speaker = p.get('speaker', 0)
            text = p.get('text', '').strip()
            
            lines.append(f"[Speaker {speaker} {timestamp}] {text}")

        self.logger.info(f"Transcript processing completed. Generated {len(lines)} lines")
        return "\n".join(lines)
    
    def generate_meeting_summary(self, transcript: str) -> str:
        """
        Generate AI summary of meeting transcript.
        
        Args:
            transcript: Meeting transcript text
            
        Returns:
            Summary text
        """
        prompt = MEETING_SUMMARY_PROMPT.format(transcript=transcript)
        
        self.logger.info("Sending transcript to LLM for summarization")
        response = self.ask_llm(prompt, max_completion_tokens=2000)
        
        if response:
            summary_md = self.extract_codeblock(response, "markdown")
            if summary_md:
                self.logger.info("AI meeting summary generated successfully")
                return summary_md
            else:
                self.logger.warning("No markdown block found in LLM response, returning full response")
                return response
        else:
            self.logger.error("Failed to get response from LLM")
            return "Failed to generate summary - LLM response was empty"