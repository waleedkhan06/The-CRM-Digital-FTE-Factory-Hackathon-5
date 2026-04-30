"""
WhatsApp Sender for AI Employee Silver Tier
Send WhatsApp messages with persistent session (authenticate once, use forever)
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class WhatsAppSender:
    """
    Send WhatsApp messages via WhatsApp Web.
    
    Session Persistence:
    - First run: Authenticate via QR code scan
    - Subsequent runs: Auto-login using saved session
    - Session lasts ~30 days before re-auth needed
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = project_root
        else:
            self.project_path = Path(project_path)
        
        self.session_path = self.project_path / 'sessions' / 'whatsapp'
        self.logs = self.project_path / 'logs'
        self.state_file = self.session_path / 'whatsapp_state.json'
        
        # Create directories
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs / f'whatsapp_sender_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize Playwright
        self.playwright = None
        self.context = None
        self.page = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Playwright with persistent session"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            
            # Launch with persistent context - this saves cookies automatically
            self.context = self.playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'  # Avoid detection
                ]
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            self.logger.info("WhatsApp Sender initialized")
            self.logger.info(f"Session path: {self.session_path}")
            
            # Check session state
            state = self._load_state()
            if state.get('authenticated'):
                self.logger.info(f"Previous auth found: {state.get('last_auth')}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            raise
    
    def _load_state(self) -> dict:
        """Load session state"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {}
    
    def _save_state(self, state: dict):
        """Save session state"""
        self.state_file.write_text(json.dumps(state, indent=2))
    
    def is_authenticated(self) -> bool:
        """Check if WhatsApp Web is authenticated"""
        try:
            # Navigate to WhatsApp Web
            self.page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
            time.sleep(3)
            
            # Multiple selectors for different WhatsApp Web versions
            selectors = [
                'div[role="grid"]',
                'div#pane-side',
                'div[aria-label="Chat list"]',
                'div._3BqNZ',
                'div._22q2x',
                'span[title="Status"]',  # Status tab
                'span[title="Communities"]',  # Communities tab
            ]
            
            for selector in selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        self.logger.info(f"✓ Authenticated (found: {selector})")
                        self._save_state({
                            'authenticated': True,
                            'last_auth': datetime.now().isoformat(),
                            'last_check': datetime.now().isoformat()
                        })
                        return True
                except:
                    continue
            
            # Fallback: check for main app structure
            content = self.page.content()
            if 'id="app"' in content and 'pane-side' in content:
                self.logger.info("✓ Authenticated (content check)")
                self._save_state({
                    'authenticated': True,
                    'last_auth': datetime.now().isoformat(),
                    'last_check': datetime.now().isoformat()
                })
                return True
            
            self.logger.debug("Not authenticated - no chat list found")
            return False
            
        except Exception as e:
            self.logger.debug(f"Auth check error: {e}")
            return False
    
    def authenticate(self, timeout: int = 120) -> bool:
        """
        Authenticate by scanning QR code

        Args:
            timeout: Seconds to wait for QR scan

        Returns:
            bool: True if authenticated
        """
        self.logger.info("Opening browser for QR code scan...")

        # Close current context
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

        from playwright.sync_api import sync_playwright

        # Start fresh playwright instance
        pw = sync_playwright().start()

        # Launch visible browser for QR scan
        temp_context = pw.chromium.launch_persistent_context(
            str(self.session_path),
            headless=False,  # Visible for QR scan
            args=['--no-sandbox', '--window-size=1280,720']
        )

        temp_page = temp_context.pages[0] if temp_context.pages else temp_context.new_page()

        print("\n" + "=" * 60)
        print("📱 SCAN QR CODE WITH WHATSAPP")
        print("=" * 60)
        print("\n1. Open WhatsApp on your phone")
        print("2. Settings > Linked Devices")
        print("3. Tap 'Link a Device'")
        print("4. Scan the QR code on screen")
        print(f"\n⏳ Waiting {timeout} seconds...\n")

        # Wait for authentication
        authenticated = False
        for i in range(timeout):
            time.sleep(1)

            if i % 5 == 0 and i > 0:
                try:
                    if temp_page.query_selector('div[role="grid"]'):
                        print(f"\n✅ AUTHENTICATED! ({i}s)")
                        authenticated = True
                        break
                except:
                    pass
                print(f"   Waiting... ({timeout-i}s)")

        # Save state
        if authenticated:
            self._save_state({
                'authenticated': True,
                'last_auth': datetime.now().isoformat(),
                'message': 'Session saved - no need to re-authenticate next time'
            })

        # Close temp context
        temp_context.close()
        pw.stop()

        # Reinitialize with fresh context
        time.sleep(2)
        self._initialize()

        return authenticated
    
    def send_message(self, phone_number: str, message: str, 
                     country_code: str = '+92') -> dict:
        """
        Send a WhatsApp message
        
        Args:
            phone_number: Phone number (without + or country code)
            message: Message to send
            country_code: Country code (default: +92 for Pakistan)
        
        Returns:
            dict: Result with status and details
        """
        try:
            # Check authentication
            if not self.is_authenticated():
                return {
                    "status": "error",
                    "message": "Not authenticated. Run: python send_whatsapp.py --auth",
                    "requires_auth": True
                }
            
            # Format phone number
            full_number = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            if not full_number.startswith(country_code.replace('+', '')):
                full_number = country_code.replace('+', '') + full_number
            
            # Navigate to send message URL
            send_url = f'https://web.whatsapp.com/send?phone={full_number}'
            self.logger.info(f"Opening chat: {send_url}")
            
            self.page.goto(send_url, wait_until='networkidle', timeout=30000)
            time.sleep(5)
            
            # Handle "clicked on phone number" popup
            try:
                continue_btn = self.page.query_selector('button:has-text("Continue")')
                if continue_btn:
                    continue_btn.click()
                    time.sleep(2)
            except:
                pass
            
            # Find message input
            try:
                message_input = self.page.wait_for_selector(
                    'div[contenteditable="true"][data-tab="10"]',
                    timeout=10000
                )
            except:
                return {
                    "status": "error",
                    "message": f"Could not find chat for {full_number}. Number may not have WhatsApp."
                }
            
            # Type message
            message_input.fill(message)
            time.sleep(1)
            
            # Click send
            send_button = self.page.query_selector('button[data-testid="compose-btn-send"]')
            if send_button:
                send_button.click()
                time.sleep(2)
                
                self.logger.info(f"Message sent to {full_number}")
                self._log_sent_message(full_number, message)
                
                return {
                    "status": "success",
                    "message": f"Message sent to +{full_number}",
                    "phone_number": full_number,
                    "message_preview": message[:100],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Could not find send button"
                }
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def send_message_by_contact(self, contact_name: str, message: str) -> dict:
        """Send message to contact by name"""
        try:
            if not self.is_authenticated():
                return {
                    "status": "error",
                    "message": "Not authenticated"
                }
            
            # Go to WhatsApp
            self.page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
            time.sleep(3)
            
            # Find and click search
            search_box = self.page.query_selector('div[contenteditable="true"][data-tab="10"]')
            if search_box:
                search_box.fill(contact_name)
                time.sleep(2)
                
                # Click first result
                contact_result = self.page.query_selector(f'span:has-text("{contact_name}")')
                if contact_result:
                    contact_result.click()
                    time.sleep(2)
                    
                    # Send message
                    message_input = self.page.query_selector('div[contenteditable="true"][data-tab="10"]')
                    if message_input:
                        message_input.fill(message)
                        time.sleep(1)
                        
                        send_button = self.page.query_selector('button[data-testid="compose-btn-send"]')
                        if send_button:
                            send_button.click()
                            
                            self.logger.info(f"Message sent to {contact_name}")
                            return {
                                "status": "success",
                                "message": f"Message sent to {contact_name}"
                            }
            
            return {
                "status": "error",
                "message": f"Contact not found: {contact_name}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def _log_sent_message(self, recipient: str, message: str):
        """Log sent message"""
        sent_folder = self.logs / 'whatsapp_sent'
        sent_folder.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = sent_folder / f'sent_{timestamp}.md'
        
        content = f"""---
type: whatsapp_sent
recipient: {recipient}
sent_at: {datetime.now().isoformat()}
---

# WhatsApp Message Sent

## To: {recipient}
## Message: {message}
"""
        log_file.write_text(content, encoding='utf-8')
    
    def close(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("WhatsApp Sender closed")
        except:
            pass


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WhatsApp Sender')
    parser.add_argument('--auth', action='store_true', help='Authenticate (scan QR code)')
    parser.add_argument('--to', type=str, help='Phone number or contact name')
    parser.add_argument('--message', type=str, help='Message to send')
    parser.add_argument('--contact', action='store_true', help='Send by contact name instead of number')
    
    args = parser.parse_args()
    
    sender = WhatsAppSender(str(project_root))
    
    if args.auth:
        print("\n📱 Authenticating...")
        if sender.authenticate():
            print("\n✅ Authentication successful!")
            print("   You can now send messages without re-authenticating.")
            print("   Session valid for ~30 days.")
        else:
            print("\n❌ Authentication failed")
    elif args.to and args.message:
        if args.contact:
            result = sender.send_message_by_contact(args.to, args.message)
        else:
            result = sender.send_message(args.to, args.message)
        print(f"\nResult: {result['status']}")
        print(f"Message: {result.get('message', '')}")
    else:
        # Interactive mode
        print("\n" + "=" * 60)
        print("📱 WhatsApp Sender - AI Employee")
        print("=" * 60)
        
        # Check auth
        if sender.is_authenticated():
            print("✓ Already authenticated!")
        else:
            print("⚠️  Not authenticated")
            print("\nRun: python whatsapp_sender.py --auth")
            sender.close()
            return
        
        # Get message details
        print("\nSend by:")
        print("1. Phone Number")
        print("2. Contact Name")
        choice = input("\nChoice (1 or 2): ").strip()
        
        if choice == '1':
            phone = input("Phone number (e.g., 923001234567): ").strip()
            message = input("Message: ").strip()
            result = sender.send_message(phone, message)
        else:
            contact = input("Contact name: ").strip()
            message = input("Message: ").strip()
            result = sender.send_message_by_contact(contact, message)
        
        print(f"\n{result}")
    
    sender.close()


if __name__ == "__main__":
    main()
