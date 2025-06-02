# src/utils/zoom_auth.py
"""Authentication utilities for Zoom recordings"""

import asyncio
import click


class ZoomAuthenticator:
    def __init__(self, tab):
        self.tab = tab
        self.cookies_accepted = False
        self.password_entered = False
    
    async def check_and_accept_cookies(self):
        """Check for cookie banner and accept if found"""
        if self.cookies_accepted:
            return True
        
        try:
            accept_button = await self.tab.find('#onetrust-accept-btn-handler', timeout=2)
            if accept_button:
                click.echo("🍪 Found cookie banner, accepting...")
                await accept_button.click()
                self.cookies_accepted = True
                await asyncio.sleep(2)
                return True
        except:
            pass
        
        return False
    
    async def check_if_logged_in(self):
        """Check if already past the password page"""
        try:
            # Check for password field
            password_input = await self.tab.find('#passcode', timeout=2)
            if password_input:
                return False
            
            # Check for video player
            player = await self.tab.find('.video-player', timeout=2)
            if player:
                return True
                
            # Check URL pattern
            current_url = await self.tab.evaluate('window.location.href')
            if '/play/' in current_url or '/rec/play' in current_url:
                return True
                
        except:
            pass
        
        return False
    
    async def enter_password(self, password, max_wait=15):
        """Enter password on the login page"""
        if await self.check_if_logged_in():
            click.echo("✅ Already logged in")
            self.password_entered = True
            return True
        
        click.echo(f"🔐 Waiting for password field ({max_wait}s max)...")
        
        # Wait for password field
        password_input = None
        for i in range(max_wait):
            await self.check_and_accept_cookies()
            
            password_input = await self.tab.find('#passcode', timeout=1)
            if not password_input:
                password_input = await self.tab.find('input[type="password"]', timeout=1)
            
            if password_input:
                break
                
            click.echo(f"\r⏱️ Waiting... {i+1}/{max_wait}s", nl=False)
        
        click.echo()
        
        if not password_input:
            return False
        
        # Enter password
        await password_input.clear_input()
        await password_input.send_keys(password)
        await asyncio.sleep(0.5)
        
        # Submit
        submit_button = await self.tab.find('#passcode_btn', timeout=5)
        if not submit_button:
            submit_button = await self.tab.find('button[type="button"]', timeout=5)
        
        if submit_button:
            await submit_button.click()
            click.echo("✅ Submitted password")
            self.password_entered = True
            await asyncio.sleep(3)
            return True
            
        return False