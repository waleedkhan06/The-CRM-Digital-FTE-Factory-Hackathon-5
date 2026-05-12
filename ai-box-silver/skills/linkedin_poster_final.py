#!/usr/bin/env python3
"""
LinkedIn Final Poster - Fixed Post Button Clicking
Waits for Post button to be enabled, uses multiple selectors
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
        
        print("\n" + "="*70)
        print("📱 LINKEDIN POSTING - FINAL VERSION")
        print("="*70)
        
        print("\n[1/7] Opening browser...")
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            str(session),
            headless=False,
            args=['--no-sandbox', '--window-size=1280,720']
        )
        page = ctx.pages[0]
        
        print("[2/7] Going to LinkedIn feed...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=120000)
        time.sleep(10)
        
        screenshot1 = logs / f'li_feed_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot1))
        print(f"    ✓ URL: {page.url[:80]}")
        
        print("\n[3/7] Clicking 'Start a post'...")
        try:
            page.click('text=Start a post', force=True, timeout=15000)
            print("    ✓ Clicked")
        except:
            print("    ⚠️  Please click 'Start a post' in browser")
        
        print("\n    ⏳ Waiting 15 seconds for dialog...")
        time.sleep(15)
        
        screenshot2 = logs / f'li_dialog_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot2))
        
        print("\n[4/7] Entering content...")
        try:
            editor = page.locator('[role="textbox"]').first
            editor.wait_for(state='visible', timeout=30000)
            editor.click()
            time.sleep(3)
            
            print("    Typing content (this takes ~30 seconds)...")
            page.keyboard.type(content[:1500], delay=50)
            time.sleep(5)
            print("    ✓ Content entered")
        except Exception as e:
            print(f"    ⚠️  {e}")
        
        screenshot3 = logs / f'li_content_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot3))
        
        print("\n[5/7] CRITICAL: Waiting for Post button to be ENABLED...")
        print("    ⏳ LinkedIn enables Post button after content is detected")
        print("    ⏳ Waiting up to 60 seconds...")

        # Wait for Post button to be enabled
        post_btn_clicked = False

        for wait_time in range(60, 0, -5):
            try:
                # Try multiple selectors for Post button
                post_btn = None

                # Selector 1: Button with "Post" text
                try:
                    post_btn = page.locator('button').filter(has_text='Post').first
                    if post_btn.is_visible(timeout=3000):
                        if post_btn.is_enabled():
                            print(f"\n    ✓ Post button found (text) - ENABLED! ({60-wait_time}s)")
                            post_btn.scroll_into_view_if_needed()
                            time.sleep(2)
                            post_btn.click(force=True)
                            print("    ✓ Post button CLICKED!")
                            post_btn_clicked = True
                            break
                        else:
                            print(f"    Post button visible but disabled... ({60-wait_time}s)")
                except:
                    pass

                # Selector 2: Button with aria-label
                if not post_btn_clicked:
                    try:
                        post_btn = page.locator('button[aria-label*="Post"]').first
                        if post_btn.is_visible(timeout=3000):
                            if post_btn.is_enabled():
                                print(f"\n    ✓ Post button found (aria) - ENABLED! ({60-wait_time}s)")
                                post_btn.click(force=True)
                                print("    ✓ Post button CLICKED!")
                                post_btn_clicked = True
                                break
                            else:
                                print(f"    Post button (aria) disabled... ({60-wait_time}s)")
                    except:
                        pass

                # Selector 3: Any button in dialog that might be Post
                if not post_btn_clicked:
                    try:
                        buttons = page.locator('div[role="dialog"] button').all()
                        for i, btn in enumerate(buttons):
                            try:
                                if btn.is_visible(timeout=2000) and btn.is_enabled():
                                    print(f"    Found enabled button in dialog... ({60-wait_time}s)")
                                    # Check if it's the Post button by position (usually last)
                                    if i == len(buttons) - 1:
                                        btn.scroll_into_view_if_needed()
                                        time.sleep(1)
                                        btn.click(force=True)
                                        print(f"    ✓ Clicked dialog button {i}!")
                                        post_btn_clicked = True
                                        break
                            except:
                                continue
                    except:
                        pass

                if not post_btn_clicked:
                    print(f"    Searching... ({60-wait_time}s)")

            except Exception as e:
                print(f"    Error checking: {e} ({60-wait_time}s)")

            time.sleep(5)

        if not post_btn_clicked:
            print("\n    ⚠️  Post button didn't become enabled automatically")
            print("    ⏳ You have 90 seconds to click 'Post' button manually")
            print("    Look for the blue 'Post' button in the dialog")
            print("    WATCH THE BROWSER WINDOW!")
            time.sleep(90)
        
        print("\n[6/7] Waiting for post to publish...")
        print("    ⏳ Waiting 30 seconds...")
        time.sleep(30)
        
        screenshot4 = logs / f'li_posted_{datetime.now().strftime("%H%M%S")}.png'
        page.screenshot(path=str(screenshot4))
        
        ctx.close()
        pw.stop()
        
        print("\n" + "="*70)
        print("✅ COMPLETE!")
        print("="*70)
        print("\n📱 Check LinkedIn: https://www.linkedin.com/feed/")
        print(f"📸 Screenshots: {logs}")
        
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
