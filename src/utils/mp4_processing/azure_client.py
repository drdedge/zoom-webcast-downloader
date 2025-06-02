"""
Azure LLM Client Module

This module provides a client for interacting with Azure OpenAI services using litellm.
It encapsulates the configuration and setup required for Azure endpoints.
"""

import os
import logging
from typing import Optional, Dict, Any
from litellm import completion
from ..logger_setup import setup_logger

logger = setup_logger(name="azure_client", level=logging.INFO)



class AzureLLMClient:
    """Client for Azure OpenAI interactions using litellm."""
    
    def __init__(self, 
                 azure_endpoint: str,
                 api_key: str,
                 model_name: str = "azure/gpt-4",
                 api_version: str = "2024-02-15-preview"):
        """
        Initialize Azure LLM client.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            model_name: Model name (e.g., "azure/gpt-4")
            api_version: API version
        """
        self.azure_endpoint = azure_endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.api_version = api_version
        self.logger = logger
        
        # Set environment variables for litellm
        self._configure_environment()
    
    def _configure_environment(self):
        """Configure environment variables for litellm."""
        os.environ["AZURE_API_KEY"] = self.api_key
        os.environ["AZURE_API_BASE"] = self.azure_endpoint
        os.environ["AZURE_API_VERSION"] = self.api_version
        self.logger.debug("Azure environment variables configured for litellm")
    
    def complete(self, 
                 prompt: str, 
                 max_completion_tokens: int = 10000,
                 reasoning_effort: str = "high",
                 **kwargs) -> Optional[str]:
        """
        Send a prompt to Azure OpenAI and get completion.
        
        Args:
            prompt: The prompt to send
            max_completion_tokens: Maximum tokens in response
            reasoning_effort: Reasoning effort level (for o3 models)
            **kwargs: Additional arguments to pass to litellm
            
        Returns:
            LLM response or None if error
        """
        try:
            self.logger.info(f"Sending prompt length: {len(prompt)} to {self.model_name}: {prompt[:50]}...")
            
            # Ensure environment is configured
            self._configure_environment()
            
            # Default parameters
            params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_completion_tokens": max_completion_tokens,
            }
            
            # Add reasoning_effort only for o3 models
            if "o3" in self.model_name.lower():
                params["reasoning_effort"] = reasoning_effort
            
            # Merge with any additional kwargs
            params.update(kwargs)
            
            response = completion(**params)
            
            result = response.choices[0].message.content
            self.logger.info("Successfully received response from LLM")
            self.logger.debug(f"Response: {result[:100]}...")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            return None
    
    def complete_with_messages(self, 
                               messages: list,
                               max_completion_tokens: int = 10000,
                               **kwargs) -> Optional[str]:
        """
        Send messages to Azure OpenAI and get completion.
        
        Args:
            messages: List of message dictionaries with role and content
            max_completion_tokens: Maximum tokens in response
            **kwargs: Additional arguments to pass to litellm
            
        Returns:
            LLM response or None if error
        """
        try:
            self.logger.info(f"Sending {len(messages)} messages to {self.model_name}")
            
            # Ensure environment is configured
            self._configure_environment()
            
            response = completion(
                model=self.model_name,
                messages=messages,
                max_completion_tokens=max_completion_tokens,
                **kwargs
            )
            
            result = response.choices[0].message.content
            self.logger.info("Successfully received response from LLM")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            return None