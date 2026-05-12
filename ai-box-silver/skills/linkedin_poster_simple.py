#!/usr/bin/env python3
"""
LinkedIn Simple Poster - Robust & Reliable
Minimal waiting, maximum reliability
"""
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Approval file')
    args = parser.parse_args()
    
    approved = project_root / 'approved'
    done = project_root / 'done'
    session = project_root / 'sessions' / 'linkedin'
    logs = project_root / 'logs'
    
    session.mkdir(parents=True, exist_ok=True)
    logs.mkdir(exist_ok=True)
    
    # Get file
    if args.file:
        fpath = Path(args.file)
    else:
        files = list(approved.glob('LINKEDIN_*.md'))
        if not files:
            print("❌ No approved posts!")
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
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("\n[1/6] Opening browser...")
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            str(session),
            headless=False,
            args=['--no-sandbox']
        )
        page = ctx.pages[0]
        
        print("[2/6] Going to LinkedIn feed...")
        page.goto('https://www.linkedin.com/feed/', timeout=30000)
        time.sleep(5)
        
        # Save screenshot
        screenshot = logs / f'li_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot))
        print(f"    ✓ URL: {page.url[:80]}")
        
        print("\n[3/6] Opening post dialog...")
        try:
            page.click('text=Start a post', timeout=10000)
            print("    ✓ Clicked")
        except:
            print("    ⚠️  Click 'Start a post' in browser")
        
        time.sleep(5)
        
        print("\n[4/6] Entering content...")
        try:
            editor = page.locator('[role="textbox"]').first
            editor.click()
            time.sleep(2)
            page.keyboard.type(content[:1500], delay=50)
            print("    ✓ Content entered")
        except Exception as e:
            print(f"    ⚠️  {e}")
            print("    Please paste content manually")
        
        time.sleep(3)
        
        print("\n[5/6] Posting...")
        try:
            post_btn = page.locator('button').filter(has_text='Post').first
            post_btn.click()
            print("    ✓ Post clicked")
        except:
            print("    ⚠️  Click 'Post' button in browser")
        
        print("\n[6/6] Waiting...")
        time.sleep(10)
        
        page.screenshot(path=str(screenshot).replace('.png', '_done.png'))
        
        ctx.close()
        pw.stop()
        
        print("\n✅ DONE!")
        print("   Check: https://www.linkedin.com/feed/")
        
        # Move to done
        done_file = done / fpath.name
        done_file.write_bytes(fpath.read_bytes())
        fpath.unlink()
        print(f"✓ Moved to: {done_file.name}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
