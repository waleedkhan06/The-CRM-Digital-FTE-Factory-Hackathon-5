#!/usr/bin/env python3
"""
LinkedIn Complete Automation - End-to-End
Combines session management + posting in one reliable flow
"""
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


def post_to_linkedin_complete(content: str):
    """
    Complete LinkedIn posting flow:
    1. Opens browser
    2. You log in (first time only)
    3. Posts automatically
    4. Saves session for next time
    """
    
    session = project_root / 'sessions' / 'linkedin'
    session.mkdir(parents=True, exist_ok=True)
    logs = project_root / 'logs'
    logs.mkdir(exist_ok=True)
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("\n" + "="*70)
        print("📱 LINKEDIN COMPLETE POSTING")
        print("="*70)
        
        print("\n[1/8] Opening browser...")
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            str(session),
            headless=False,
            slow_mo=100,
            args=['--no-sandbox', '--window-size=1280,720']
        )
        page = ctx.pages[0]
        
        print("[2/8] Going to LinkedIn...")
        page.goto('https://www.linkedin.com/', wait_until='networkidle', timeout=60000)
        time.sleep(5)
        
        # Check if logged in
        if 'login' in page.url:
            print("\n" + "="*70)
            print("⚠️  NEEDS LOGIN")
            print("="*70)
            print("\n📋 PLEASE LOG IN:")
            print("1. Enter email")
            print("2. Enter password")
            print("3. Complete verification")
            print("4. Wait for feed")
            print("5. SCROLL feed (saves session)")
            print("\n⏳ Waiting 120 seconds...")
            print("-"*70)
            
            for i in range(120, 0, -1):
                time.sleep(1)
                if i % 30 == 0:
                    print(f"   {i}s remaining...")
                
                # Check if redirected to feed
                if '/feed/' in page.url and 'login' not in page.url:
                    print(f"\n✅ Logged in!")
                    break
            
            # Take screenshot
            screenshot = logs / f'li_auth_{datetime.now().strftime("%H%M%S")}.png'
            screenshot.write_bytes(page.screenshot())
        
        print("[3/8] Navigating to feed...")
        page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=60000)
        time.sleep(5)
        
        screenshot1 = logs / f'li_feed_{datetime.now().strftime("%H%M%S")}.png'
        screenshot1.write_bytes(page.screenshot())
        print(f"    ✓ URL: {page.url}")
        
        print("\n[4/8] Starting post...")
        # Click "Start a post"
        try:
            page.click('text=Start a post', force=True)
            print("    ✓ Clicked 'Start a post'")
        except:
            print("    ⚠️  Please click 'Start a post' in browser")
        
        time.sleep(5)
        
        screenshot2 = logs / f'li_dialog_{datetime.now().strftime("%H%M%S")}.png'
        screenshot2.write_bytes(page.screenshot())
        
        print("\n[5/8] Entering content...")
        # Find editor
        try:
            editor = page.locator('[role="textbox"]').first
            editor.wait_for(state='visible', timeout=15000)
            editor.click()
            time.sleep(2)
            
            # Type content
            print("    Typing content...")
            page.keyboard.type(content[:2000], delay=50)
            time.sleep(2)
            print("    ✓ Content entered")
        except Exception as e:
            print(f"    ⚠️  Editor issue: {e}")
            print("    Please paste content manually")
        
        screenshot3 = logs / f'li_content_{datetime.now().strftime("%H%M%S")}.png'
        screenshot3.write_bytes(page.screenshot())
        
        print("\n[6/8] Posting...")
        # Click Post button
        try:
            post_btn = page.locator('button').filter(has_text='Post').first
            post_btn.wait_for(state='visible', timeout=15000)
            post_btn.scroll_into_view_if_needed()
            time.sleep(2)
            post_btn.click(force=True)
            print("    ✓ Post button clicked")
        except:
            print("    ⚠️  Please click 'Post' button in browser")
        
        print("\n[7/8] Waiting for post to publish...")
        time.sleep(10)
        
        screenshot4 = logs / f'li_posted_{datetime.now().strftime("%H%M%S")}.png'
        screenshot4.write_bytes(page.screenshot())
        
        print("\n[8/8] Saving session...")
        time.sleep(5)
        
        ctx.close()
        pw.stop()
        
        print("\n" + "="*70)
        print("✅ COMPLETE!")
        print("="*70)
        print("\n📱 Check LinkedIn:")
        print("   https://www.linkedin.com/feed/")
        print("\n📸 Screenshots:")
        print(f"   {logs}")
        print("\n💾 Session saved for next time!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Approval file')
    args = parser.parse_args()
    
    approved = project_root / 'approved'
    done = project_root / 'done'
    
    if args.file:
        fpath = Path(args.file)
    else:
        files = list(approved.glob('LINKEDIN_*.md'))
        if not files:
            print("❌ No approved posts!")
            return
        fpath = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    print(f"\n📄 File: {fpath.name}")
    
    txt = fpath.read_text()
    if '## Post Content' in txt:
        content = txt.split('## Post Content')[1].strip().replace('```', '').strip()
    else:
        content = txt[:1000]
    
    print(f"\n📝 Content ({len(content)} chars):")
    print("-"*60)
    print(content[:200] + "..." if len(content) > 200 else content)
    print("-"*60)
    
    ok = post_to_linkedin_complete(content)
    
    if ok:
        done_file = done / fpath.name
        done_file.write_bytes(fpath.read_bytes())
        fpath.unlink()
        print(f"\n✓ Moved to: {done_file.name}")
    else:
        print("\n⚠️  File left in approved/")


if __name__ == "__main__":
    main()
