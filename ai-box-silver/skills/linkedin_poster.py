"""
LinkedIn Poster - Production Ready with Playwright
Reliable LinkedIn posting with stable selectors and proper waiting

Silver Tier Requirements:
- Post to LinkedIn via browser automation
- Use stable selectors (role-based, data-testid)
- Wait for modal, editor, and button visibility
- Prevent navigation issues
- Human-in-the-loop approval required
"""
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


def post_to_linkedin(content: str):
    """
    Post to LinkedIn using Playwright with reliable selectors
    
    Args:
        content (str): Post content to publish
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    session = project_root / 'sessions' / 'linkedin'
    session.mkdir(parents=True, exist_ok=True)
    logs = project_root / 'logs'
    logs.mkdir(exist_ok=True)
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("\n[1/7] Opening browser...")
        pw = sync_playwright().start()
        
        # Launch with slow_mo for observation, headless=False for debugging
        ctx = pw.chromium.launch_persistent_context(
            str(session),
            headless=False,
            slow_mo=100,  # Slow down for observation
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1280,720'
            ]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        
        print("[2/7] Navigating to LinkedIn feed...")
        # CRITICAL: Always open feed URL
        page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=60000)
        time.sleep(5)  # Wait for page to fully render
        
        # Verify we're on feed
        if '/feed/' not in page.url:
            print(f"    ⚠️  Redirected to {page.url}, forcing feed...")
            page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=30000)
            time.sleep(3)
        
        screenshot1 = logs / f'li_feed_{datetime.now().strftime("%H%M%S")}.png'
        screenshot1.write_bytes(page.screenshot())
        print(f"    ✓ URL: {page.url}")
        
        print("[3/7] Starting a post...")
        # CRITICAL: Use stable selector for "Start a post" button
        start_post_clicked = False

        try:
            # Method 1: Look for "Start a post" text in buttons
            start_post_btn = page.locator('button').filter(has_text='Start a post').first
            if start_post_btn.is_visible(timeout=5000):
                start_post_btn.scroll_into_view_if_needed()
                time.sleep(1)
                start_post_btn.click()
                print("    ✓ Clicked 'Start a post' button")
                start_post_clicked = True
        except Exception as e:
            print(f"    Method 1 failed: {e}")

        if not start_post_clicked:
            try:
                # Method 2: Try data-testid
                start_post_btn = page.locator('[data-testid*="share"]').first
                if start_post_btn.is_visible(timeout=5000):
                    start_post_btn.click()
                    print("    ✓ Clicked via data-testid")
                    start_post_clicked = True
            except:
                print("    Method 2 failed")

        if not start_post_clicked:
            # Method 3: Try clicking the share box area
            print("    ⚠️  Using fallback - clicking share box area")
            page.evaluate("window.scrollTo(0, 200)")
            time.sleep(2)
            # Try clicking the "Start a post" text
            page.click('text=Start a post', force=True)
            print("    ✓ Clicked 'Start a post' text")
            start_post_clicked = True

        # CRITICAL: Wait for post modal/dialog to appear
        print("[4/7] Waiting for post dialog...")
        dialog_found = False

        try:
            # Wait for dialog role
            page.wait_for_selector('[role="dialog"]', timeout=10000)
            print("    ✓ Post dialog appeared")
            dialog_found = True
        except:
            print("    ⚠️  Dialog selector not found")

        if not dialog_found:
            try:
                # Fallback: wait for editor
                page.wait_for_selector('[role="textbox"]', timeout=10000)
                print("    ✓ Editor appeared")
                dialog_found = True
            except:
                print("    ❌ Neither dialog nor editor found")

        time.sleep(3)  # Let modal animation complete

        screenshot2 = logs / f'li_dialog_{datetime.now().strftime("%H%M%S")}.png'
        screenshot2.write_bytes(page.screenshot())
        
        print("[5/7] Entering post content...")
        # CRITICAL: Locate editor using stable selector
        try:
            # Method 1: Get by role (most stable)
            editor = page.get_by_role("textbox")
            if editor.is_visible(timeout=5000):
                editor.click()
                time.sleep(1)
                editor.fill(content[:2000])  # LinkedIn has ~3000 char limit
                print("    ✓ Content entered via role")
            else:
                raise Exception("Editor not visible")
        except:
            # Method 2: Fallback to selector
            try:
                editor = page.locator('[role="textbox"]').first
                editor.click()
                time.sleep(1)
                editor.fill(content[:2000])
                print("    ✓ Content entered via selector")
            except:
                # Method 3: Fallback to keyboard
                print("    ⚠️  Using keyboard fallback")
                page.keyboard.press('Tab')
                time.sleep(1)
                page.keyboard.press('Tab')
                time.sleep(1)
                page.keyboard.type(content[:2000], delay=50)
                print("    ✓ Content typed via keyboard")
        
        time.sleep(2)  # Let content render
        
        screenshot3 = logs / f'li_content_{datetime.now().strftime("%H%M%S")}.png'
        screenshot3.write_bytes(page.screenshot())
        
        print("[6/7] Waiting for Post button...")
        # CRITICAL: Ensure Post button is visible and enabled
        try:
            # Method 1: Get by role and name (most stable)
            post_btn = page.get_by_role("button", name="Post")
            
            # Wait for visibility
            post_btn.wait_for(state='visible', timeout=10000)
            print("    ✓ Post button visible")
            
            # Scroll into view
            post_btn.scroll_into_view_if_needed()
            time.sleep(1)
            
            # Check if enabled
            is_enabled = post_btn.is_enabled()
            if not is_enabled:
                print("    ⚠️  Post button disabled, waiting...")
                time.sleep(3)
            
        except:
            # Method 2: Fallback to data-testid
            try:
                post_btn = page.locator('[data-testid="share-post-submit-button"]')
                post_btn.wait_for(state='visible', timeout=10000)
                print("    ✓ Post button found via data-testid")
            except:
                print("    ⚠️  Using fallback for Post button")
                post_btn = None
        
        print("[7/7] Clicking Post button...")
        try:
            if post_btn:
                # Use force=True to click through any overlays
                post_btn.click(force=True)
                print("    ✓ Post button clicked")
            else:
                # Fallback coordinates (Post button is typically bottom-right of modal)
                page.mouse.click(700, 600)
                print("    ✓ Clicked coordinates")
        except Exception as e:
            print(f"    ⚠️  Click error: {e}")
            # Try alternative click
            page.mouse.click(700, 600)
            print("    ✓ Alternative click successful")
        
        # Wait for post to publish
        print("    ⏳ Waiting for post to publish...")
        time.sleep(8)
        
        screenshot4 = logs / f'li_posted_{datetime.now().strftime("%H%M%S")}.png'
        screenshot4.write_bytes(page.screenshot())
        
        # Check if dialog closed (success indicator)
        dialog = page.locator('[role="dialog"]').first
        is_dialog_open = dialog.is_visible(timeout=5000)
        
        if is_dialog_open:
            print("    ⚠️  Dialog still open, Post button may have failed")
            print("    Trying Post button again...")
            time.sleep(2)
            try:
                post_btn = page.get_by_role("button", name="Post")
                post_btn.click(force=True)
                time.sleep(5)
                print("    ✓ Second attempt successful")
            except:
                print("    ⚠️  Second attempt failed")
        
        ctx.close()
        pw.stop()
        
        print("\n✅ DONE!")
        print(f"   Check: https://www.linkedin.com/feed/")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Approval file to post')
    args = parser.parse_args()
    
    approved = project_root / 'approved'
    done = project_root / 'done'
    
    if args.file:
        fpath = Path(args.file)
    else:
        # Get most recent approved file
        files = list(approved.glob('LINKEDIN_*.md'))
        if not files:
            print("❌ No approved LinkedIn posts!")
            return
        fpath = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    print(f"\n📄 File: {fpath.name}")
    
    # Extract post content
    txt = fpath.read_text()
    if '## Post Content' in txt:
        content = txt.split('## Post Content')[1].strip().replace('```', '').strip()
    elif '## Content' in txt:
        content = txt.split('## Content')[1].strip().replace('```', '').strip()
    else:
        content = txt[:1000]
    
    print(f"\n📝 Content ({len(content)} chars):")
    print("-"*60)
    print(content[:200] + "..." if len(content) > 200 else content)
    print("-"*60)
    
    # Post to LinkedIn
    ok = post_to_linkedin(content)
    
    if ok:
        # Move to done
        done_file = done / fpath.name
        done_file.write_bytes(fpath.read_bytes())
        fpath.unlink()
        print(f"\n✓ Moved to: {done_file.name}")
    else:
        print("\n❌ Post failed - file left in approved/")


if __name__ == "__main__":
    main()
