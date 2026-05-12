#!/usr/bin/env python3
"""
LinkedIn Keep-Alive Session
Keeps browser session alive for reliable posting
"""
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
session_path = project_root / 'sessions' / 'linkedin'
session_path.mkdir(parents=True, exist_ok=True)

print("\n" + "="*70)
print("📱 LINKEDIN SESSION KEEPER")
print("="*70)
print("\nThis will:")
print("1. Open browser")
print("2. You log in ONCE")
print("3. Browser stays open (session stays alive)")
print("4. You can post multiple times")
print("5. Close browser when done")

try:
    from playwright.sync_api import sync_playwright
    
    print("\n[1/3] Opening browser...")
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        str(session_path),
        headless=False,
        args=[
            '--no-sandbox',
            '--window-size=1280,720',
            '--disable-dev-shm-usage'
        ]
    )
    page = ctx.pages[0]
    
    print("[2/3] Going to LinkedIn...")
    page.goto('https://www.linkedin.com/login', wait_until='networkidle', timeout=60000)
    time.sleep(3)
    
    print("\n" + "="*70)
    print("📋 LOG IN TO LINKEDIN")
    print("="*70)
    print("\n⚠️  BROWSER IS OPEN")
    print("\nWhat to do:")
    print("1. Enter your LinkedIn email")
    print("2. Enter your password")
    print("3. Click 'Sign in'")
    print("4. Complete any verification")
    print("5. Wait for your feed to load")
    print("6. SCROLL through feed (important!)")
    print("7. Stay on this page - DON'T CLOSE BROWSER")
    print("\n⏳ I'll keep the session alive...")
    print("-"*70)
    
    # Wait for feed
    for i in range(60, 0, -1):
        time.sleep(1)
        if i % 10 == 0:
            print(f"   Session alive... {i}s")
        
        # Check if on feed
        if '/feed/' in page.url and 'login' not in page.url:
            if i < 50:  # Only show success once
                print(f"\n✅ Logged in! Session active")
                print(f"   URL: {page.url}")
    
    # Take screenshot
    screenshot = project_root / 'logs' / f'linkedin_session_{int(time.time())}.png'
    page.screenshot(path=str(screenshot))
    print(f"\n✓ Screenshot: {screenshot.name}")
    
    print("\n" + "="*70)
    print("✅ SESSION ACTIVE!")
    print("="*70)
    print(f"\n✓ Logged in to: {page.url}")
    print("✓ Session will stay alive")
    print("✓ You can now run: python -m skills.linkedin_poster")
    print("\n⚠️  KEEP BROWSER OPEN!")
    print("   Closing browser will end the session")
    
    # Keep alive
    print("\n⏳ Keeping session alive... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(30)
            # Refresh session
            page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)
            print("   Session refreshed...")
    except KeyboardInterrupt:
        print("\n\nStopping session keeper...")
    
    ctx.close()
    pw.stop()
    
    print("\n" + "="*70)
    print("✅ SESSION ENDED")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
