#!/usr/bin/env python3
"""
Zoom Recording Capture & Download Script
Captures the recording info request and downloads the MP4 file
"""

import time
import asyncio
import json
import os
import re
import click
from datetime import datetime, timezone
from urllib.parse import urlparse
import nodriver as uc
from curl_cffi import requests as curl_requests

# Browser fingerprint settings
IMPERSONATE_PROFILE = "chrome116"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)

# Global variables for captured data
extracted_vars = {}
all_requests = []
target_request_found = False
password_entered = False
cookies_accepted = False
browser = None
tab = None


def check_if_complete():
    """Check if we have all required variables"""
    return bool(
        extracted_vars.get('RECORDING_INFO_URL') and 
        extracted_vars.get('COOKIES_STR') and 
        extracted_vars.get('CSRF_TOKEN')
    )


async def check_and_accept_cookies():
    """Check for cookie banner and accept if found"""
    global cookies_accepted
    
    if cookies_accepted:
        return True
    
    try:
        accept_button = await tab.find('#onetrust-accept-btn-handler', timeout=2)
        if accept_button:
            click.echo("🍪 Found cookie banner, accepting...")
            await accept_button.click()
            cookies_accepted = True
            await asyncio.sleep(2)
            click.echo("✅ Cookies accepted")
            
            # Try to capture browser cookies immediately after accepting
            await capture_browser_cookies()
            return True
    except:
        pass
    
    return False


async def check_if_logged_in():
    """Check if we're already past the password page"""
    try:
        # Check if password field exists
        password_input = await tab.find('#passcode', timeout=2)
        if password_input:
            return False
        
        # Check if we're on the recording page (no password field)
        # Look for video player or recording elements
        player = await tab.find('.video-player', timeout=2)
        if player:
            return True
            
        # Check URL - if it contains 'play' or similar, we're likely logged in
        current_url = await tab.evaluate('window.location.href')
        if '/play/' in current_url or '/rec/play' in current_url:
            return True
            
    except:
        pass
    
    return False


async def capture_browser_cookies():
    """Get all cookies from the browser and update extracted_vars"""
    try:
        # Use CDP to get cookies
        cookies_response = await tab.send(uc.cdp.network.get_cookies())
        
        if cookies_response:
            cookie_str = "; ".join([f"{cookie.name}={cookie.value}" for cookie in cookies_response])
            
            if cookie_str:
                extracted_vars['COOKIES_STR'] = cookie_str
                click.echo(f"✅ Captured browser cookies ({len(cookie_str)} chars)")
                
                # Check if we now have everything
                if check_if_complete():
                    click.echo("✅ All variables now complete!")
                    save_extracted_variables()
                
                return cookie_str
    except Exception as e:
        click.echo(f"⚠️ Could not get browser cookies: {e}")
    
    return ""


async def on_request(event):
    """Capture all requests and look for the recording info request"""
    global target_request_found, extracted_vars
    
    request_data = {
        'url': event.request.url,
        'method': event.request.method,
        'headers': dict(event.request.headers) if event.request.headers else {},
        'timestamp': datetime.now(timezone.utc),
        'request_id': event.request_id,
    }
    
    all_requests.append(request_data)
    
    # Check if this is the recording info request
    if "/nws/recording/1.0/play/info/" in event.request.url:
        click.echo(f"\n{'='*60}")
        click.echo("🎯 FOUND TARGET REQUEST!")
        click.echo(f"{'='*60}")
        
        target_request_found = True
        headers = request_data['headers']
        
        # Extract all needed variables
        recording_url = event.request.url
        cookies_from_headers = headers.get('cookie', '') or headers.get('Cookie', '')
        referer = headers.get('referer', '') or headers.get('Referer', '')
        csrf = headers.get('zoom-csrftoken', '') or headers.get('Zoom-Csrftoken', '') or headers.get('ZOOM-CSRFTOKEN', '')
        
        # Extract recording ID and origin
        parsed_url = urlparse(recording_url)
        origin = f"https://{parsed_url.netloc}"
        path_parts = parsed_url.path.split('/')
        recording_id = ""
        if 'info' in path_parts:
            info_index = path_parts.index('info')
            if info_index + 1 < len(path_parts):
                recording_id = path_parts[info_index + 1].split('?')[0]
        
        # Update extracted vars
        extracted_vars['RECORDING_INFO_URL'] = recording_url
        extracted_vars['REFERER_URL'] = referer
        extracted_vars['CSRF_TOKEN'] = csrf
        extracted_vars['RECORDING_ID'] = recording_id
        extracted_vars['ORIGIN'] = origin
        
        # Use cookies from headers if available, otherwise keep existing browser cookies
        if cookies_from_headers:
            extracted_vars['COOKIES_STR'] = cookies_from_headers
        
        # Display what we captured
        click.echo(f"📍 URL: {recording_url[:100]}...")
        click.echo(f"🍪 Cookies: {len(cookies_from_headers)} chars from headers")
        click.echo(f"🔐 CSRF Token: {csrf}")
        click.echo(f"🌐 Origin: {origin}")
        
        # If no cookies from headers, try to get browser cookies
        if not cookies_from_headers and not extracted_vars.get('COOKIES_STR'):
            click.echo("⚠️ No cookies in request headers, getting browser cookies...")
            await capture_browser_cookies()
        
        # Check if we have all required fields
        if check_if_complete():
            click.echo(f"\n✅ All variables captured successfully!")
        else:
            missing = []
            if not extracted_vars.get('COOKIES_STR'):
                missing.append("COOKIES")
            if not extracted_vars.get('CSRF_TOKEN'):
                missing.append("CSRF_TOKEN")
            click.echo(f"\n⚠️ WARNING: Missing {', '.join(missing)}")
        
        save_extracted_variables()


async def on_response(event):
    """Capture recording info response to get MP4 URL"""
    global extracted_vars
    
    if "/nws/recording/1.0/play/info/" in event.response.url and event.response.status == 200:
        try:
            body_result = await tab.send(uc.cdp.network.get_response_body(event.request_id))
            if body_result and body_result[0]:
                data = json.loads(body_result[0])
                if 'result' in data and 'mp4Url' in data['result']:
                    extracted_vars['MP4_URL'] = data['result']['mp4Url']
                    extracted_vars['FILE_INFO'] = {
                        'duration_ms': data['result'].get('duration'),
                        'file_size': data['result'].get('fileSize'),
                        'meeting_topic': data['result'].get('meetingTopic', '')
                    }
                    click.echo("✅ Captured MP4 URL from response")
                    save_extracted_variables()
                    
                    # Check if we now have everything
                    if check_if_complete():
                        click.echo("✅ All variables now complete!")
        except Exception as e:
            click.echo(f"⚠️ Could not parse response: {e}")


def save_extracted_variables():
    """Save extracted variables to file"""
    output_dir = extracted_vars.get('OUTPUT_DIR', 'output')
    click.echo("💾 Saving extracted variables...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON
    json_file = os.path.join(output_dir, f"extracted_variables_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_vars, f, indent=2, ensure_ascii=False)
    
    # Save as Python file
    py_file = os.path.join(output_dir, "zoom_recording_config.py")
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write("Zoom Recording Configuration\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n")
        f.write('"""\n\n')
        for key, value in extracted_vars.items():
            if key not in ['MP4_URL', 'FILE_INFO']:  # Skip these for config file
                if isinstance(value, str):
                    escaped_value = value.replace('"', '\\"')
                    f.write(f'{key} = "{escaped_value}"\n')
    
    click.echo(f"💾 Variables saved to {output_dir}/")


async def enter_password(password):
    """Enter password if on password page"""
    global password_entered
    
    # Check if already logged in
    if await check_if_logged_in():
        click.echo("✅ Already logged in, skipping password entry")
        password_entered = True
        return True
    
    click.echo("🔐 Waiting for password field (15 seconds max)...")
    
    # Wait up to 15 seconds for password field
    start_time = datetime.now()
    password_input = None
    
    while (datetime.now() - start_time).seconds < 15:
        # Check for cookie banner on login screen
        if not cookies_accepted:
            await check_and_accept_cookies()
        
        password_input = await tab.find('#passcode', timeout=2)
        if not password_input:
            password_input = await tab.find('input[type="password"]', timeout=2)
        
        if password_input:
            click.echo("✅ Found password input")
            break
            
        elapsed = (datetime.now() - start_time).seconds
        click.echo(f"\r⏱️ Waiting for password field... {elapsed}/15s", nl=False)
        await asyncio.sleep(1)
    
    click.echo()  # New line
    
    if not password_input:
        click.echo("⚠️ Password field not found after 15 seconds")
        return False
    
    # Enter password
    await password_input.clear_input()
    await password_input.send_keys(password)
    await asyncio.sleep(0.5)
    
    # Find and click submit button
    submit_button = await tab.find('#passcode_btn', timeout=5)
    if not submit_button:
        submit_button = await tab.find('button[type="button"]', timeout=5)
    
    if submit_button:
        await submit_button.click()
        click.echo("✅ Submitted password")
        password_entered = True
        await asyncio.sleep(3)  # Wait for login to process
        return True
    else:
        click.echo("⚠️ Submit button not found")
    
    return False


def download_recording(output_filename=None):
    """Download the recording using captured credentials"""
    
    if not check_if_complete():
        click.echo("❌ Missing required credentials for download")
        return False
    
    click.echo(f"\n{'='*60}")
    click.echo("📥 Starting Download")
    click.echo(f"{'='*60}")
    
    # Create session
    session = curl_requests.Session(impersonate=IMPERSONATE_PROFILE)
    
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Origin": extracted_vars['ORIGIN'],
        "Referer": extracted_vars['REFERER_URL'],
    })
    
    # Set cookies
    for cookie in extracted_vars['COOKIES_STR'].split(';'):
        if '=' in cookie:
            key, value = cookie.strip().split('=', 1)
            session.cookies.set(key, value)
    
    # Get MP4 URL if we don't have it
    if not extracted_vars.get('MP4_URL'):
        click.echo("📡 Getting recording info...")
        
        response = session.get(
            extracted_vars['RECORDING_INFO_URL'],
            headers={
                "x-requested-with": "XMLHttpRequest, OWASP CSRFGuard Project",
                "zoom-csrftoken": extracted_vars['CSRF_TOKEN'],
            },
            timeout=30
        )
        
        if response.status_code != 200:
            click.echo(f"❌ Failed to get recording info: {response.status_code}")
            click.echo(f"Response: {response.text[:500]}...")
            return False
        
        try:
            data = response.json()
            if 'result' in data and 'mp4Url' in data['result']:
                extracted_vars['MP4_URL'] = data['result']['mp4Url']
                extracted_vars['FILE_INFO'] = {
                    'duration_ms': data['result'].get('duration'),
                    'file_size': data['result'].get('fileSize'),
                    'meeting_topic': data['result'].get('meetingTopic', '')
                }
            else:
                click.echo("❌ No MP4 URL in response")
                return False
        except Exception as e:
            click.echo(f"❌ Failed to parse response: {e}")
            return False
    
    # Generate filename if needed
    output_dir = extracted_vars.get('OUTPUT_DIR', 'output')
    if not output_filename:
        meeting_topic = extracted_vars.get('FILE_INFO', {}).get('meeting_topic', 'recording')
        safe_topic = "".join(c for c in meeting_topic if c.isalnum() or c in ' -_')[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{safe_topic}_{timestamp}.mp4")
    else:
        output_file = os.path.join(output_dir, output_filename)
    
    extracted_vars['OUTPUT_FILENAME'] = output_file
    
    # Show file info
    if extracted_vars.get('FILE_INFO'):
        info = extracted_vars['FILE_INFO']
        if info.get('duration_ms'):
            click.echo(f"📹 Duration: {info['duration_ms'] / 60000:.1f} minutes")
        if info.get('file_size'):
            click.echo(f"📦 Expected size: {info['file_size'] / 1048576:.1f} MB")
    
    click.echo(f"💾 Downloading to: {output_file}")
    
    # Download with progress
    resp = session.get(extracted_vars['MP4_URL'], stream=True, timeout=30)
    
    if resp.status_code != 200:
        click.echo(f"❌ Download failed: {resp.status_code}")
        return False
    
    total_size = int(resp.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
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
    
    # Verify file
    if os.path.exists(output_file):
        actual_size = os.path.getsize(output_file)
        click.echo(f"📁 File saved: {output_file} ({actual_size / 1048576:.1f} MB)")
        return True
    
    return False


async def wait_for_variables(timeout_seconds=30):
    """Wait for variables with periodic cookie banner checks"""
    global cookies_accepted
    
    start_time = datetime.now()
    last_cookie_check = 0
    last_browser_cookie_check = 0
    
    while (datetime.now() - start_time).seconds < timeout_seconds:
        elapsed = (datetime.now() - start_time).seconds
        
        # Check if we already have everything
        if check_if_complete():
            return True
        
        # Check for cookie banner every 5 seconds
        if not cookies_accepted and elapsed - last_cookie_check >= 5:
            await check_and_accept_cookies()
            last_cookie_check = elapsed
        
        # Try to get browser cookies every 10 seconds if we don't have them
        if not extracted_vars.get('COOKIES_STR') and elapsed - last_browser_cookie_check >= 10:
            await capture_browser_cookies()
            last_browser_cookie_check = elapsed
        
        click.echo(f"\r⏱️ Waiting... {elapsed}/{timeout_seconds}s (Requests: {len(all_requests)}) {'🍪' if cookies_accepted else '  '}", nl=False)
        await asyncio.sleep(1)
    
    click.echo()  # New line after progress
    return check_if_complete()


async def capture_and_download(url, password, output_dir, output_filename, headless, timeout):
    """Main function to capture credentials and download recording"""
    global browser, tab, target_request_found, password_entered, cookies_accepted, extracted_vars
    
    # Store in extracted_vars for later use
    extracted_vars['OUTPUT_DIR'] = output_dir
    
    click.echo("🚀 Zoom Recording Capture & Download")
    click.echo(f"📍 URL: {url[:80]}...")
    click.echo(f"🔑 Password: {'*' * len(password)}")
    click.echo(f"📁 Output: {output_dir}/")
    click.echo(f"🖥️ Headless: {headless}")
    click.echo("="*60)
    
    # Create browser
    browser = await uc.Browser.create(headless=headless)
    tab = browser.main_tab
    
    try:
        # Enable network capture
        await tab.send(uc.cdp.network.enable(max_post_data_size=1000000))
        tab.add_handler(uc.cdp.network.RequestWillBeSent, on_request)
        tab.add_handler(uc.cdp.network.ResponseReceived, on_response)
        click.echo("✅ Network capture enabled")
        
        # First attempt
        attempt = 1
        while attempt <= 2:
            click.echo(f"\n📌 Attempt {attempt}/2")
            
            # Navigate to URL (only on first attempt)
            if attempt == 1:
                click.echo(f"🌐 Navigating to Zoom recording...")
                await tab.get(url)
                await asyncio.sleep(3)
            
            # Enter password if needed
            if not password_entered:
                success = await enter_password(password)
                if not success and attempt == 1:
                    click.echo("⚠️ Password field not found, refreshing page...")
                    await tab.reload()
                    await asyncio.sleep(3)
                    attempt += 1
                    continue
            else:
                click.echo("ℹ️ Already logged in, skipping password entry")
            
            # Wait for variables with cookie banner tracking
            click.echo(f"\n⏳ Waiting for recording info request ({timeout} seconds)...")
            success = await wait_for_variables(timeout)
            
            if success:
                click.echo("\n✅ Successfully captured all required data!")
                break
            
            # If first attempt failed and we don't have complete data
            if attempt == 1 and not check_if_complete():
                click.echo("\n⚠️ Did not capture required data, refreshing page...")
                await tab.reload()
                await asyncio.sleep(3)
                
                # Check if we need to accept cookies again after refresh
                if not cookies_accepted:
                    await check_and_accept_cookies()
                
                attempt += 1
            else:
                click.echo("\n❌ Failed to capture required data after 2 attempts")
                return False
        
        # Close browser before downloading
        click.echo("\n🔄 Closing browser...")
        await browser.stop()
        click.echo("\n🔄 Browser closed...")
        browser = None
        
        # Save all captured data
        save_extracted_variables()
        
        # Display captured variables
        click.echo(f"\n{'='*60}")
        click.echo("📋 CAPTURED VARIABLES:")
        click.echo(f"{'='*60}")
        for key, value in extracted_vars.items():
            if key in ['MP4_URL', 'FILE_INFO']:
                continue
            if isinstance(value, str):
                display_value = value[:100] + '...' if len(value) > 100 else value
                click.echo(f"{key}: {display_value}")
        click.echo(f"{'='*60}")
        
        # Download the recording
        return download_recording(output_filename)
        
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if browser:
            try:
                await browser.stop()
            except Exception:
                pass  # Browser might already be closed

@click.command()
@click.option('--url', '-u', required=True, help='Zoom recording URL')
@click.option('--password', '-p', required=True, help='Recording password')
@click.option('--output-dir', '-o', default='output', help='Output directory (default: output)')
@click.option('--output-filename', '-f', default=None, help='Output filename (default: auto-generated)')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--timeout', '-t', default=30, type=int, help='Timeout in seconds (default: 30)')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(url, password, output_dir, output_filename, headless, timeout, debug):
    """Capture and download Zoom recordings"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the async function
    success = asyncio.run(capture_and_download(url, password, output_dir, output_filename, headless, timeout))
    
    if success:
        click.echo(f"\n{'='*60}")
        click.echo("✅ SUCCESS!")
        click.echo(f"{'='*60}")
        click.echo(f"📁 Recording saved to: {extracted_vars.get('OUTPUT_FILENAME', output_dir)}")
        click.echo(f"📄 Variables saved to: {output_dir}/")
        click.echo(f"{'='*60}")
    else:
        click.echo(f"\n{'='*60}")
        click.echo("❌ FAILED!")
        click.echo(f"{'='*60}")
        click.echo("Could not capture credentials or download recording.")
        click.echo("Please check:")
        click.echo("  1. The URL is correct")
        click.echo("  2. The password is correct")
        click.echo("  3. You have access to the recording")
        click.echo(f"{'='*60}")
        
        # Save debug info if requested
        if debug:
            debug_file = os.path.join(output_dir, f"debug_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(debug_file, 'w') as f:
                json.dump({
                    'all_requests': all_requests,
                    'captured_vars': extracted_vars,
                    'password_entered': password_entered,
                    'cookies_accepted': cookies_accepted
                }, f, indent=2)
            click.echo(f"\nDebug info saved to: {debug_file}")


if __name__ == "__main__":
    main()