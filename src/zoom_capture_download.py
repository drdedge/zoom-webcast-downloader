#!/usr/bin/env python3
"""
Zoom Recording Capture & Download Script
Captures the recording info request and downloads the MP4 file
"""

import time
import asyncio
import json
import os
import click
from datetime import datetime
import nodriver as uc

# Import utilities
from utils.zoom_download.zoom_auth import ZoomAuthenticator
from utils.zoom_download.zoom_capture import ZoomNetworkCapture
from utils.zoom_download.zoom_download import ZoomDownloader
from utils.config_manager import ConfigManager  # Add this import

# Global browser instance
browser = None
tab = None


def save_variables(variables, output_dir):
    """Save extracted variables to files"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON
    json_file = os.path.join(output_dir, f"zoom_recording_vars_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(variables, f, indent=2, ensure_ascii=False)
    
    # Save as Python config
    py_file = os.path.join(output_dir, "zoom_config.py")
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('"""Zoom Recording Configuration"""\n\n')
        for key, value in variables.items():
            if isinstance(value, str):
                f.write(f'{key} = "{value}"\n')
    
    return json_file, py_file


async def wait_for_variables(capture, auth, timeout_seconds=30):
    """Wait for variables with periodic cookie banner checks"""
    start_time = datetime.now()
    last_cookie_check = 0
    last_browser_cookie_check = 0
    
    while (datetime.now() - start_time).seconds < timeout_seconds:
        elapsed = (datetime.now() - start_time).seconds
        
        # Check if we already have everything
        if capture.check_if_complete():
            return True
        
        # Check for cookie banner every 5 seconds
        if not auth.cookies_accepted and elapsed - last_cookie_check >= 5:
            await auth.check_and_accept_cookies()
            last_cookie_check = elapsed
        
        # Try to get browser cookies every 10 seconds if we don't have them
        if not capture.extracted_vars.get('COOKIES_STR') and elapsed - last_browser_cookie_check >= 10:
            await capture.capture_browser_cookies(tab)
            last_browser_cookie_check = elapsed
        
        click.echo(f"\r⏱️ Waiting... {elapsed}/{timeout_seconds}s (Requests: {len(capture.all_requests)}) {'🍪' if auth.cookies_accepted else '  '}", nl=False)
        await asyncio.sleep(1)
    
    click.echo()  # New line after progress
    return capture.check_if_complete()


async def capture_and_download(url, password, output_dir, output_filename, headless, timeout, config):
    """Main function to capture credentials and download recording"""
    global browser, tab
    
    click.echo("🚀 Zoom Recording Capture & Download")
    click.echo(f"📍 URL: {url[:80]}...")
    click.echo(f"🔑 Password: {'*' * len(password)}")
    click.echo(f"📁 Output: {output_dir}/")
    click.echo(f"🖥️ Headless: {headless}")
    click.echo("="*60)
    
    # Create instances
    capture = ZoomNetworkCapture()
    auth = None
    
    # Create browser
    browser = await uc.Browser.create(headless=headless)
    tab = browser.main_tab
    
    # Create authenticator with tab
    auth = ZoomAuthenticator(tab)
    
    try:
        # Enable network capture
        await tab.send(uc.cdp.network.enable(max_post_data_size=1000000))
        
        # Add handlers
        tab.add_handler(uc.cdp.network.RequestWillBeSent, capture.create_request_handler())
        tab.add_handler(uc.cdp.network.ResponseReceived, capture.create_response_handler(tab))
        
        click.echo("✅ Network capture enabled")
        
        # Get max wait from config
        max_wait_password = config.zoom_download.max_wait_password if config else 15
        
        # First attempt
        attempt = 1
        max_attempts = config.zoom_download.retry.max_attempts if config else 2
        
        while attempt <= max_attempts:
            click.echo(f"\n📌 Attempt {attempt}/{max_attempts}")
            
            # Navigate to URL (only on first attempt)
            if attempt == 1:
                click.echo(f"🌐 Navigating to Zoom recording...")
                await tab.get(url)
                await asyncio.sleep(3)
            
            # Enter password if needed
            if not auth.password_entered:
                success = await auth.enter_password(password, max_wait_password)
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
            success = await wait_for_variables(capture, auth, timeout)
            
            if success:
                click.echo("\n✅ Successfully captured all required data!")
                break
            
            # If first attempt failed and we don't have complete data
            if attempt < max_attempts and not capture.check_if_complete():
                click.echo(f"\n⚠️ Did not capture required data, refreshing page...")
                await tab.reload()
                await asyncio.sleep(3)
                
                # Check if we need to accept cookies again after refresh
                if not auth.cookies_accepted:
                    await auth.check_and_accept_cookies()
                
                attempt += 1
            else:
                click.echo(f"\n❌ Failed to capture required data after {max_attempts} attempts")
                return False
        
        # Close browser before downloading
        if browser:
            try:
                click.echo("\n🔄 Closing browser...")
                # Check if stop() is async or sync
                stop_result = browser.stop()
                if asyncio.iscoroutine(stop_result):
                    await stop_result
                click.echo("✅ Browser closed")
            except Exception as e:
                click.echo(f"⚠️ Browser close error (ignoring): {e}")
            finally:
                browser = None
        
        # Save all captured data
        capture.extracted_vars['OUTPUT_DIR'] = output_dir
        
        # Save variables if configured to do so
        if config and config.zoom_download.output.save_variables:
            json_file, py_file = save_variables(capture.extracted_vars, output_dir)
            click.echo(f"💾 Variables saved to {output_dir}/")
        
        # Display captured variables
        click.echo(f"\n{'='*60}")
        click.echo("📋 CAPTURED VARIABLES:")
        click.echo(f"{'='*60}")
        for key, value in capture.extracted_vars.items():
            if key in ['MP4_URL', 'FILE_INFO']:
                continue
            if isinstance(value, str):
                display_value = value[:100] + '...' if len(value) > 100 else value
                click.echo(f"{key}: {display_value}")
        click.echo(f"{'='*60}")
        
        # Download the recording
        downloader = ZoomDownloader(capture.extracted_vars, output_dir, config)
        download_file = downloader.download(output_filename)
        
        if download_file:
            capture.extracted_vars['OUTPUT_FILENAME'] = download_file
            return True
        
        # If download failed but we have credentials, it's still a partial success
        if capture.check_if_complete():
            click.echo("\n⚠️ Download failed but credentials were captured successfully")
            click.echo("You can use the saved credentials to download manually")
            return True
        
        return False
        
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if we at least captured the credentials successfully
        if capture and capture.check_if_complete():
            click.echo("\n⚠️ Error occurred but credentials were captured successfully")
            capture.extracted_vars['OUTPUT_DIR'] = output_dir
            if config and config.zoom_download.output.save_variables:
                save_variables(capture.extracted_vars, output_dir)
                click.echo(f"💾 Variables saved to {output_dir}/")
            return True  # Partial success
        
        return False
    
    finally:
        if browser:
            try:
                # Check if stop() is async or sync
                stop_result = browser.stop()
                if asyncio.iscoroutine(stop_result):
                    await stop_result
                click.echo("✅ Browser closed")
            except:
                pass  # Browser might already be closed


@click.command()
@click.option('--url', '-u', required=True, help='Zoom recording URL')
@click.option('--password', '-p', required=True, help='Recording password')
@click.option('--config', '-c', help='Configuration file path')
@click.option('--output-dir', '-o', help='Output directory (overrides config)')
@click.option('--output-filename', '-f', default=None, help='Output filename (default: auto-generated)')
@click.option('--headless/--no-headless', default=None, help='Run browser in headless mode')
@click.option('--timeout', '-t', type=int, help='Timeout in seconds')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(url, password, config, output_dir, output_filename, headless, timeout, debug):
    """Capture and download Zoom recordings"""
    
    # Load configuration
    config_mgr = ConfigManager(config_file=config)
    
    # Override with command line arguments if provided
    if output_dir is not None:
        config_mgr.config.output_dir = output_dir
    if headless is not None:
        config_mgr.config.zoom_download.headless = headless
    if timeout is not None:
        config_mgr.config.zoom_download.timeout = timeout
    if debug:
        config_mgr.config.debug = debug
    
    # Get final values from config
    actual_output_dir = config_mgr.config.output_dir
    actual_headless = config_mgr.config.zoom_download.headless
    actual_timeout = config_mgr.config.zoom_download.timeout
    
    # Create output directory
    os.makedirs(actual_output_dir, exist_ok=True)
    
    # Run the async function, passing the entire config object
    success = asyncio.run(
        capture_and_download(
            url, 
            password, 
            actual_output_dir, 
            output_filename, 
            actual_headless, 
            actual_timeout,
            config_mgr.config  # Pass the entire config object
        )
    )
    
    if success:
        click.echo(f"\n{'='*60}")
        click.echo("✅ SUCCESS!")
        click.echo(f"{'='*60}")
        if os.path.exists(os.path.join(actual_output_dir, "zoom_config.py")):
            click.echo(f"📄 Variables saved to: {actual_output_dir}/")
        # Check if download completed by looking for MP4 files
        mp4_files = [f for f in os.listdir(actual_output_dir) if f.endswith('.mp4')]
        if mp4_files:
            click.echo(f"📁 Recording downloaded: {mp4_files[-1]}")
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
        if debug and config_mgr.config.debug:
            debug_file = os.path.join(actual_output_dir, f"debug_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            click.echo(f"\nDebug mode enabled - check {debug_file} for details")


if __name__ == "__main__":
    main()