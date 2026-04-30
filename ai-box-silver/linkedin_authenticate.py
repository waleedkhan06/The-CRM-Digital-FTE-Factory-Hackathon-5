#!/usr/bin/env python3
"""
LinkedIn Authentication - One-time browser login
Opens browser, you log in, session is saved for future use
"""
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
session_path = project_root / 'sessions' / 'linkedin'
session_path.mkdir(parents=True, exist_ok=True)

print("\n" + "="*70)
print("📱 LINKEDIN AUTHENTICATION")
print("="*70)
print("\nThis will:")
print("1. Open browser")
print("2. You log in to LinkedIn")
print("3. Session saved for future posts")
print("4. One-time setup (valid ~30 days)")

try:
    from playwright.sync_api import sync_playwright
    
    print("\n[1/3] Opening browser...")
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        str(session_path),
        headless=False,
        slow_mo=100,
        args=['--no-sandbox', '--window-size=1280,720']
    )
    page = ctx.pages[0]
    
    print("[2/3] Navigating to LinkedIn...")
    page.goto('https://www.linkedin.com/login', wait_until='networkidle', timeout=60000)
    time.sleep(3)
    
    print("\n" + "="*70)
    print("📋 STEP 3: LOG IN TO LINKEDIN")
    print("="*70)
    print("\n⚠️  BROWSER WINDOW IS OPEN")
    print("\nWhat to do:")
    print("1. Enter your LinkedIn email")
    print("2. Enter your password")
    print("3. Click 'Sign in'")
    print("4. Complete any verification")
    print("5. Make sure you see your LinkedIn feed")
    print("6. Wait 10 seconds for session to save")
    print("\n⏳ Waiting 180 seconds (3 minutes) for you to log in...")
    print("-"*70)
    print("\n💡 TIP: Take your time to:")
    print("   - Enter email correctly")
    print("   - Enter password")
    print("   - Complete any 2FA verification")
    print("   - Wait for feed to load")
    print("   - Scroll through feed briefly")
    print("   - This ensures session is saved properly")
    print("-"*70)

    for i in range(180, 0, -1):
        time.sleep(1)
        if i % 30 == 0:
            print(f"   {i} seconds remaining...")
        elif i == 10:
            print(f"   {i} seconds - almost done!")
    
    # Take screenshot to verify
    screenshot = project_root / 'logs' / f'linkedin_auth_{int(time.time())}.png'
    page.screenshot(path=str(screenshot))
    print(f"\n✓ Screenshot saved: {screenshot.name}")
    
    # Verify we're logged in
    print("\n[3/3] Verifying authentication...")
    page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=30000)
    time.sleep(5)

    # Take screenshot
    screenshot = project_root / 'logs' / f'linkedin_auth_success_{int(time.time())}.png'
    page.screenshot(path=str(screenshot))

    # Check if on feed
    if '/feed/' in page.url and 'login' not in page.url:
        print("\n" + "="*70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*70)
        print(f"\n✓ Logged in to: {page.url}")
        print("✓ Session saved to: sessions/linkedin/")
        print("✓ Valid for ~30 days")
        print("✓ Screenshot: logs/linkedin_auth_success_*.png")
        print("\n📱 You can now post to LinkedIn!")
        print("\nNext steps:")
        print("1. Create post: nano needs_action/LINKEDIN_POST.md")
        print("2. Run watcher: python watchers/linkedin_watcher.py")
        print("3. Approve: mv pending_approval/*.md approved/")
        print("4. Post: python -m skills.linkedin_poster")
    else:
        print("\n⚠️  Not properly logged in")
        print(f"   Current URL: {page.url}")
        print("\nPlease try again:")
        print("1. Make sure you entered correct credentials")
        print("2. Complete any 2FA verification")
        print("3. Wait for feed to fully load")
        print("4. Run: python linkedin_authenticate.py")

    print("\n⏳ Keeping browser open for 10 more seconds...")
    time.sleep(10)

    ctx.close()
    pw.stop()

    print("\n" + "="*70)
    print("✅ DONE!")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure browser opened")
    print("2. Complete LinkedIn login")
    print("3. Wait for feed to load")
    print("4. Try again if needed")
