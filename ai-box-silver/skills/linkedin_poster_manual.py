#!/usr/bin/env python3
"""
LinkedIn Poster - Simple & Reliable
Keeps browser session alive, you manually click "Post"
"""
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


def post_to_linkedin_manual(content: str):
    """
    Post to LinkedIn with manual assistance
    Opens browser, you help click Post button if needed
    """
    
    session = project_root / 'sessions' / 'linkedin'
    session.mkdir(parents=True, exist_ok=True)
    logs = project_root / 'logs'
    logs.mkdir(exist_ok=True)
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("\n[1/5] Opening browser with saved session...")
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            str(session),
            headless=False,
            slow_mo=200,  # Slow down for observation
            args=['--no-sandbox', '--window-size=1280,720']
        )
        page = ctx.pages[0]
        
        print("[2/5] Going to LinkedIn feed...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)
        
        screenshot1 = logs / f'li_feed_{datetime.now().strftime("%H%M%S")}.png'
        screenshot1.write_bytes(page.screenshot())
        print(f"    ✓ URL: {page.url}")
        
        print("\n[3/5] Opening post dialog...")
        print("    ⚠️  WATCH THE BROWSER WINDOW")
        print("    If 'Start a post' dialog doesn't open:")
        print("    1. Click 'Start a post' button manually")
        print("    2. Wait for dialog to open")
        print("\n    Attempting automatic click...")
        
        # Try to click "Start a post"
        try:
            page.click('text=Start a post', force=True, timeout=10000)
            print("    ✓ Clicked 'Start a post'")
        except:
            print("    ⚠️  Please click 'Start a post' manually in browser")
        
        time.sleep(5)  # Wait for dialog
        
        screenshot2 = logs / f'li_dialog_{datetime.now().strftime("%H%M%S")}.png'
        screenshot2.write_bytes(page.screenshot())
        
        print("\n[4/5] Entering content...")
        print("    Content will be typed automatically...")
        
        # Find editor and type
        try:
            editor = page.locator('[role="textbox"]').first
            editor.wait_for(state='visible', timeout=10000)
            editor.click()
            time.sleep(2)
            
            # Type content slowly
            for char in content[:1500]:
                page.keyboard.type(char, delay=50)
                if len(content) > 100 and (content.index(char) % 100 == 0):
                    time.sleep(0.1)
            
            print("    ✓ Content entered")
        except Exception as e:
            print(f"    ⚠️  Editor issue: {e}")
            print("    Please paste this content manually:")
            print("-"*60)
            print(content[:500])
            print("-"*60)
        
        time.sleep(3)
        
        screenshot3 = logs / f'li_content_{datetime.now().strftime("%H%M%S")}.png'
        screenshot3.write_bytes(page.screenshot())
        
        print("\n[5/5] Posting to LinkedIn...")
        print("    ⚠️  WATCH THE BROWSER WINDOW")
        print("    If 'Post' button doesn't click automatically:")
        print("    1. Click the blue 'Post' button manually")
        print("    2. Wait for confirmation")
        print("\n    Attempting automatic click...")
        
        # Try to click Post button
        try:
            post_btn = page.locator('button').filter(has_text='Post').first
            post_btn.wait_for(state='visible', timeout=10000)
            post_btn.click(force=True)
            print("    ✓ Post button clicked")
        except:
            print("    ⚠️  Please click 'Post' button manually in browser")
        
        print("\n⏳ Waiting 15 seconds for post to publish...")
        print("    WATCH BROWSER: If you see 'Post' button, click it!")
        time.sleep(15)
        
        screenshot4 = logs / f'li_posted_{datetime.now().strftime("%H%M%S")}.png'
        screenshot4.write_bytes(page.screenshot())
        
        ctx.close()
        pw.stop()
        
        print("\n" + "="*70)
        print("✅ DONE!")
        print("="*70)
        print("\n📱 Check your LinkedIn feed:")
        print("   https://www.linkedin.com/feed/")
        print("\n📸 Screenshots saved to:")
        print(f"   {logs}")
        print("\n✅ If you clicked Post manually, it's published!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Approval file to post')
    args = parser.parse_args()
    
    approved = project_root / 'approved'
    done = project_root / 'done'
    
    if args.file:
        fpath = Path(args.file)
    else:
        files = list(approved.glob('LINKEDIN_*.md'))
        if not files:
            print("❌ No approved LinkedIn posts!")
            return
        fpath = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    print(f"\n📄 File: {fpath.name}")
    
    # Extract content
    txt = fpath.read_text()
    if '## Post Content' in txt:
        content = txt.split('## Post Content')[1].strip().replace('```', '').strip()
    else:
        content = txt[:1000]
    
    print(f"\n📝 Content ({len(content)} chars):")
    print("-"*60)
    print(content[:200] + "..." if len(content) > 200 else content)
    print("-"*60)
    
    # Post
    ok = post_to_linkedin_manual(content)
    
    if ok:
        done_file = done / fpath.name
        done_file.write_bytes(fpath.read_bytes())
        fpath.unlink()
        print(f"\n✓ Moved to: {done_file.name}")


if __name__ == "__main__":
    main()
