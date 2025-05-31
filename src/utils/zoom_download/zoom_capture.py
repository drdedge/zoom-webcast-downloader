# src/utils/zoom_capture.py
"""Network capture utilities for Zoom recordings"""

import json
from datetime import datetime, timezone
from urllib.parse import urlparse
import click
import nodriver as uc


class ZoomNetworkCapture:
    def __init__(self):
        self.extracted_vars = {}
        self.all_requests = []
        self.target_found = False
    
    def check_if_complete(self):
        """Check if we have all required variables"""
        return bool(
            self.extracted_vars.get('RECORDING_INFO_URL') and 
            self.extracted_vars.get('COOKIES_STR') and 
            self.extracted_vars.get('CSRF_TOKEN')
        )
    
    async def capture_browser_cookies(self, tab):
        """Get cookies from browser"""
        try:
            cookies_response = await tab.send(uc.cdp.network.get_cookies())
            
            if cookies_response:
                cookie_str = "; ".join([
                    f"{cookie.name}={cookie.value}" 
                    for cookie in cookies_response
                ])
                
                if cookie_str:
                    self.extracted_vars['COOKIES_STR'] = cookie_str
                    click.echo(f"✅ Captured browser cookies ({len(cookie_str)} chars)")
                    return cookie_str
        except Exception as e:
            click.echo(f"⚠️ Could not get browser cookies: {e}")
        
        return ""
    
    def create_request_handler(self):
        """Create the request handler function"""
        async def on_request(event):
            request_data = {
                'url': event.request.url,
                'method': event.request.method,
                'headers': dict(event.request.headers) if event.request.headers else {},
                'timestamp': datetime.now(timezone.utc),
                'request_id': event.request_id,
            }
            
            self.all_requests.append(request_data)
            
            # Check if this is the recording info request
            if "/nws/recording/1.0/play/info/" in event.request.url:
                click.echo("\n🎯 FOUND TARGET REQUEST!")
                self.target_found = True
                
                headers = request_data['headers']
                recording_url = event.request.url
                
                # Extract variables
                parsed_url = urlparse(recording_url)
                origin = f"https://{parsed_url.netloc}"
                
                # Get recording ID
                path_parts = parsed_url.path.split('/')
                recording_id = ""
                if 'info' in path_parts:
                    idx = path_parts.index('info')
                    if idx + 1 < len(path_parts):
                        recording_id = path_parts[idx + 1].split('?')[0]
                
                # Update extracted vars
                self.extracted_vars.update({
                    'RECORDING_INFO_URL': recording_url,
                    'REFERER_URL': headers.get('referer', '') or headers.get('Referer', ''),
                    'CSRF_TOKEN': (headers.get('zoom-csrftoken', '') or 
                                  headers.get('Zoom-Csrftoken', '') or 
                                  headers.get('ZOOM-CSRFTOKEN', '')),
                    'RECORDING_ID': recording_id,
                    'ORIGIN': origin,
                })
                
                # Use cookies from headers if available
                cookies_from_headers = headers.get('cookie', '') or headers.get('Cookie', '')
                if cookies_from_headers:
                    self.extracted_vars['COOKIES_STR'] = cookies_from_headers
                
                click.echo(f"✅ Captured request data")
        
        return on_request
    
    def create_response_handler(self, tab):
        """Create the response handler function"""
        async def on_response(event):
            if ("/nws/recording/1.0/play/info/" in event.response.url and 
                event.response.status == 200):
                try:
                    body_result = await tab.send(
                        uc.cdp.network.get_response_body(event.request_id)
                    )
                    if body_result and body_result[0]:
                        data = json.loads(body_result[0])
                        if 'result' in data and 'mp4Url' in data['result']:
                            self.extracted_vars['MP4_URL'] = data['result']['mp4Url']
                            self.extracted_vars['FILE_INFO'] = {
                                'duration_ms': data['result'].get('duration'),
                                'file_size': data['result'].get('fileSize'),
                                'meeting_topic': data['result'].get('meetingTopic', '')
                            }
                            click.echo("✅ Captured MP4 URL from response")
                except Exception as e:
                    click.echo(f"⚠️ Could not parse response: {e}")
        
        return on_response