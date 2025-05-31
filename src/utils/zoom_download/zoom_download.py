# src/utils/zoom_download.py
"""Download utilities for Zoom recordings"""

import os
import click
from curl_cffi import requests as curl_requests
from datetime import datetime


class ZoomDownloader:
    def __init__(self, extracted_vars, output_dir='output', config=None):
        self.vars = extracted_vars
        self.output_dir = output_dir
        self.config = config
        
        # Get browser settings from config or use defaults
        if config:
            self.impersonate_profile = config.zoom_download.browser.impersonate_profile
            self.user_agent = config.zoom_download.browser.user_agent
            self.chunk_size = config.zoom_download.retry.chunk_size
        else:
            # Fallback defaults if no config provided
            self.impersonate_profile = "chrome116"
            self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
            self.chunk_size = 8192    
    def check_requirements(self):
        """Check if we have all required data"""
        required = ['RECORDING_INFO_URL', 'COOKIES_STR', 'CSRF_TOKEN', 'ORIGIN', 'REFERER_URL']
        missing = [key for key in required if not self.vars.get(key)]
        
        if missing:
            click.echo(f"❌ Missing required data: {', '.join(missing)}")
            return False
        return True
    
    def get_mp4_url(self):
        """Get MP4 URL from recording info endpoint"""
        if self.vars.get('MP4_URL'):
            return True
        
        click.echo("📡 Getting recording info...")
        
        session = curl_requests.Session(impersonate=self.impersonate_profile)
        session.headers.update({
            "User-Agent": self.user_agent,
            "Origin": self.vars['ORIGIN'],
            "Referer": self.vars['REFERER_URL'],
        })
        
        # Set cookies
        for cookie in self.vars['COOKIES_STR'].split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                session.cookies.set(key, value)
        
        response = session.get(
            self.vars['RECORDING_INFO_URL'],
            headers={
                "x-requested-with": "XMLHttpRequest, OWASP CSRFGuard Project",
                "zoom-csrftoken": self.vars['CSRF_TOKEN'],
            },
            timeout=30
        )
        
        if response.status_code != 200:
            click.echo(f"❌ Failed to get recording info: {response.status_code}")
            return False
        
        try:
            data = response.json()
            if 'result' in data and 'mp4Url' in data['result']:
                self.vars['MP4_URL'] = data['result']['mp4Url']
                self.vars['FILE_INFO'] = {
                    'duration_ms': data['result'].get('duration'),
                    'file_size': data['result'].get('fileSize'),
                    'meeting_topic': data['result'].get('meetingTopic', '')
                }
                return True
        except Exception as e:
            click.echo(f"❌ Failed to parse response: {e}")
        
        return False
    
    def download(self, output_filename=None):
        """Download the recording"""
        if not self.check_requirements():
            return False
        
        if not self.get_mp4_url():
            return False
        
        # Generate filename
        if not output_filename:
            topic = self.vars.get('FILE_INFO', {}).get('meeting_topic', 'recording')
            safe_topic = "".join(c for c in topic if c.isalnum() or c in ' -_')[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{safe_topic}_{timestamp}.mp4"
        
        output_file = os.path.join(self.output_dir, output_filename)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Show file info
        if self.vars.get('FILE_INFO'):
            info = self.vars['FILE_INFO']
            if info.get('duration_ms'):
                click.echo(f"📹 Duration: {info['duration_ms'] / 60000:.1f} minutes")
            if info.get('file_size'):
                click.echo(f"📦 Expected size: {info['file_size'] / 1048576:.1f} MB")
        
        click.echo(f"💾 Downloading to: {output_file}")
        
        # Download
        session = curl_requests.Session(impersonate=self.impersonate_profile)
        session.headers.update({
            "User-Agent": self.user_agent,
            "Origin": self.vars['ORIGIN'],
            "Referer": self.vars['REFERER_URL'],
        })
        
        # Set cookies
        for cookie in self.vars['COOKIES_STR'].split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                session.cookies.set(key, value)
        
        resp = session.get(self.vars['MP4_URL'], stream=True, timeout=30)
        
        if resp.status_code != 200:
            click.echo(f"❌ Download failed: {resp.status_code}")
            return False
        
        total_size = int(resp.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = int(100 * downloaded / total_size)
                        mb_down = downloaded / 1048576
                        mb_total = total_size / 1048576
                        click.echo(f"\r⏬ Progress: {percent}% ({mb_down:.1f}/{mb_total:.1f} MB)", 
                                  nl=False)
        
        resp.close()
        click.echo(f"\n✅ Download complete!")
        
        if os.path.exists(output_file):
            actual_size = os.path.getsize(output_file)
            click.echo(f"📁 File saved: {output_file} ({actual_size / 1048576:.1f} MB)")
            return output_file
        
        return None