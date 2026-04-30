#!/usr/bin/env python3
"""
LinkedIn Robust Poster - Long Timeouts, Maximum Reliability
Gives you plenty of time to help if needed
"""
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Approval file')
    parser.add_argument('--manual', action='store_true', help='Wait for manual help')
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
        
        print("\n" + "="*70)
        print("📱 LINKEDIN POSTING - LONG TIMEOUT MODE")
        print("="*70)
        
        print("\n[1/8] Opening browser...")
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            str(session),
            headless=False,
            slow_mo=100,  # Slow down for reliability
            args=['--no-sandbox', '--window-size=1280,720']
        )
        page = ctx.pages[0]
        
        print("[2/8] Going to LinkedIn feed...")
        print("    ⏳ This may take up to 60 seconds...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=120000)
        time.sleep(10)  # Wait for page to fully load
        
        # Save screenshot
        screenshot = logs / f'li_feed_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot))
        print(f"    ✓ URL: {page.url[:80]}")
        
        print("\n[3/8] Waiting for page stability...")
        print("    ⏳ Waiting 15 seconds...")
        time.sleep(15)
        
        print("\n[4/8] Opening post dialog...")
        print("    ⏳ Attempting to click 'Start a post'...")
        try:
            # Try multiple times
            for attempt in range(5):
                try:
                    page.click('text=Start a post', timeout=10000, force=True)
                    print(f"    ✓ Clicked on attempt {attempt+1}")
                    break
                except:
                    print(f"    Attempt {attempt+1} failed, retrying...")
                    time.sleep(3)
            else:
                print("    ⚠️  Please click 'Start a post' button in browser")
                print("    ⏳ Waiting 60 seconds for you to click...")
                time.sleep(60)
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
        
        time.sleep(10)  # Wait for dialog to open
        
        screenshot2 = logs / f'li_dialog_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot2))
        
        print("\n[5/8] Entering content...")
        print("    ⏳ This will take 30-60 seconds...")
        try:
            # Wait for editor with long timeout
            editor = page.locator('[role="textbox"]').first
            editor.wait_for(state='visible', timeout=60000)
            print("    ✓ Editor found")
            
            editor.click()
            time.sleep(3)
            
            # Type slowly and reliably
            print("    Typing content...")
            for i in range(0, len(content[:1500]), 50):
                chunk = content[i:i+50]
                page.keyboard.type(chunk, delay=50)
                if i % 200 == 0 and i > 0:
                    print(f"    {i}/{len(content[:1500])} characters typed...")
                    time.sleep(1)
            
            time.sleep(5)  # Let content render
            print("    ✓ Content entered successfully")
            
        except Exception as e:
            print(f"    ⚠️  Editor issue: {e}")
            print("    ⏳ You have 60 seconds to paste content manually")
            print("    Content to paste:")
            print("-"*60)
            print(content[:500])
            print("-"*60)
            time.sleep(60)
        
        screenshot3 = logs / f'li_content_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot3))
        
        print("\n[6/8] Preparing to post...")
        print("    ⏳ Waiting 10 seconds for Post button to be ready...")
        time.sleep(10)
        
        print("\n[7/8] Clicking Post button...")
        print("    ⏳ Attempting to click...")
        try:
            # Try multiple times
            for attempt in range(5):
                try:
                    post_btn = page.locator('button').filter(has_text='Post').first
                    post_btn.wait_for(state='visible', timeout=10000)
                    post_btn.scroll_into_view_if_needed()
                    time.sleep(2)
                    post_btn.click(force=True)
                    print(f"    ✓ Post clicked on attempt {attempt+1}")
                    break
                except:
                    print(f"    Attempt {attempt+1} failed, retrying...")
                    time.sleep(5)
            else:
                print("    ⚠️  Please click the blue 'Post' button in browser")
                print("    ⏳ Waiting 90 seconds for you to click...")
                time.sleep(90)
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
        
        print("\n[8/8] Waiting for post to publish...")
        print("    ⏳ Waiting 30 seconds...")
        time.sleep(30)
        
        screenshot4 = logs / f'li_posted_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot4))
        
        ctx.close()
        pw.stop()
        
        print("\n" + "="*70)
        print("✅ COMPLETE!")
        print("="*70)
        print("\n📱 Check your LinkedIn feed:")
        print("   https://www.linkedin.com/feed/")
        print("\n📸 Screenshots saved to:")
        print(f"   {logs}")
        print("\n💾 Session saved for next time!")
        
        # Move to done
        done_file = done / fpath.name
        done_file.write_bytes(fpath.read_bytes())
        fpath.unlink()
        print(f"\n✓ Moved to: {done_file.name}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
