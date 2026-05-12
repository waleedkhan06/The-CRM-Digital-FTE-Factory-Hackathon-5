"""
WhatsApp Watcher for AI Employee Silver Tier - PRODUCTION MODE
Monitors WhatsApp Web for new messages with keywords and creates action items

Human-in-the-Loop (HITL) Implementation:
- All incoming messages create action files in /needs_action for human review
- High priority messages also create notifications in /pending_approval
- Outgoing messages require explicit approval via approval request files
- No automatic replies - all responses need human approval
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from watchers.base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages with specific keywords.
    
    HITL Enforcement:
    - Incoming messages -> /needs_action/ (for human review)
    - High priority -> Also creates /pending_approval/ notification
    - Outgoing replies -> Require approval file in /pending_approval/
    """
    
    def __init__(self, project_path: str = None, check_interval: int = 30):
        if project_path is None:
            self.project_path = project_root
        else:
            self.project_path = Path(project_path)
        
        self.needs_action = self.project_path / 'needs_action'
        self.pending_approval = self.project_path / 'pending_approval'
        self.check_interval = check_interval
        self.processed_messages = set()
        
        # Keywords to watch for
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'meeting', 'deadline']
        
        # Setup logging
        log_dir = self.project_path / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f'whatsapp_watcher_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create required directories
        self.needs_action.mkdir(exist_ok=True)
        self.pending_approval.mkdir(exist_ok=True)
        self.session_path = self.project_path / 'sessions' / 'whatsapp'
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # Load configuration from .env
        self._load_config()
        
        # Initialize Playwright
        self.browser = None
        self.context = None
        self.page = None
        if not self.demo_mode:
            self._initialize_playwright()
    
    def _load_config(self):
        """Load configuration from .env file"""
        env_file = self.project_path / '.env'
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        self.whatsapp_enabled = os.getenv('WHATSAPP_ENABLED', 'true').lower() == 'true'
        self.check_interval = int(os.getenv('WHATSAPP_WATCHER_INTERVAL', '30'))
        self.demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
        
        # Load custom keywords
        keywords_str = os.getenv('WHATSAPP_KEYWORDS', '')
        if keywords_str:
            self.keywords = [k.strip().lower() for k in keywords_str.split(',')]
        
        self.logger.info(f"WhatsApp enabled: {self.whatsapp_enabled}")
        self.logger.info(f"Demo mode: {self.demo_mode}")
        self.logger.info(f"Keywords: {', '.join(self.keywords)}")
        self.logger.info("HITL: All messages require human review")
    
    def _initialize_playwright(self):
        """Initialize Playwright browser"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            
            self.context = self.playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Show browser for QR code
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            self.logger.info("Playwright initialized successfully")
            self.logger.info(f"Session path: {self.session_path}")
            self.logger.info("Browser window opened - scan QR code if prompted")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright: {e}")
            raise
    
    def check_for_updates(self) -> list:
        """Check for new WhatsApp messages with keywords"""
        if not self.whatsapp_enabled or self.demo_mode:
            return self._demo_check()

        try:
            messages = []

            # Navigate to WhatsApp Web
            try:
                self.page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
                time.sleep(5)  # Give extra time for page to fully load
            except Exception as e:
                self.logger.warning(f"Could not load WhatsApp Web: {e}")
                return []

            # Wait for chat list to load - try multiple selectors
            chat_list_found = False
            chat_selectors = [
                'div[role="grid"]',  # Standard ARIA grid
                'div[x-tab="chats"]',  # Tab-based selector
                'div#pane-side',  # Side pane selector
                'div._3BqNZ',  # Class-based (older)
                'div[aria-label="Chat list"]',  # ARIA label
                'div._22q2x',  # Alternative class
            ]

            for selector in chat_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.logger.debug(f"Found chat list with selector: {selector}")
                    chat_list_found = True
                    break
                except:
                    continue

            if not chat_list_found:
                self.logger.warning("Chat list not found with any known selector")
                # Take screenshot for debugging
                try:
                    screenshot = self.project_path / 'logs' / f'whatsapp_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    self.page.screenshot(path=str(screenshot))
                    self.logger.info(f"Screenshot saved: {screenshot}")
                except:
                    pass
                return []

            time.sleep(2)  # Extra wait after finding chat list

            # Find all chat elements - try multiple approaches
            try:
                chats = []
                chat_row_selectors = [
                    'div[role="grid"] div[role="row"]',
                    'div#pane-side div[role="row"]',
                    'div._3BqNZ div[role="row"]',
                    'div._22q2x div[role="row"]',
                    'div[aria-label*="unread"]',  # Unread chats
                    'div._3521e',  # Alternative chat row class
                ]

                for selector in chat_row_selectors:
                    try:
                        chats = self.page.query_selector_all(selector)
                        if chats:
                            self.logger.debug(f"Found {len(chats)} chats with: {selector}")
                            break
                    except:
                        continue

                if not chats:
                    # Last resort: try to find any clickable chat element
                    chats = self.page.query_selector_all('div[role="row"]:has-text(.)')
                    self.logger.debug(f"Found {len(chats)} chats (fallback)")

                self.logger.info(f"Total chats found: {len(chats)}")

                # Process each chat
                for i, chat in enumerate(chats[:15]):  # Check up to 15 chats
                    try:
                        chat_text = chat.inner_text(timeout=2000)

                        # Check for unread indicator
                        is_unread = False
                        try:
                            # Try multiple unread indicators
                            unread_selectors = [
                                'span[aria-label*="unread"]',
                                'span._3521e',
                                'div._3521e',
                                'span:has-text("unread")',
                            ]
                            for sel in unread_selectors:
                                try:
                                    unread_badge = chat.query_selector(sel)
                                    if unread_badge:
                                        is_unread = True
                                        break
                                except:
                                    continue
                        except:
                            pass

                        # Check if any keyword is present
                        chat_text_lower = chat_text.lower()
                        matched_keywords = [kw for kw in self.keywords if kw in chat_text_lower]

                        if matched_keywords:
                            chat_name = self._extract_chat_name(chat)

                            msg_id = hash(f"{chat_name}:{chat_text}:{datetime.now().strftime('%Y-%m-%d %H')}")

                            if msg_id not in self.processed_messages:
                                self.processed_messages.add(msg_id)
                                messages.append({
                                    'chat_name': chat_name,
                                    'text': chat_text[:500],
                                    'matched_keywords': matched_keywords,
                                    'timestamp': datetime.now().isoformat(),
                                    'is_unread': is_unread
                                })
                                self.logger.info(f"✓ Matched from {chat_name}: {matched_keywords}")

                    except Exception as e:
                        self.logger.debug(f"Error processing chat {i}: {e}")
                        continue

            except Exception as e:
                self.logger.error(f"Error finding chats: {e}")

            return messages

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            return []
    
    def _extract_chat_name(self, chat_element) -> str:
        """Extract chat name from chat element"""
        try:
            aria_label = chat_element.get_attribute('aria-label', timeout=1000)
            if aria_label:
                return aria_label.split(',')[0].strip()
            return "Unknown Contact"
        except:
            return "Unknown Contact"
    
    def _demo_check(self) -> list:
        """Demo mode - check for demo message files"""
        demo_file = self.project_path / 'inbox' / 'whatsapp_message.txt'
        if demo_file.exists():
            content = demo_file.read_text().strip()
            demo_file.unlink()
            
            return [{
                'chat_name': 'Demo Contact',
                'text': content,
                'matched_keywords': [kw for kw in self.keywords if kw in content.lower()],
                'timestamp': datetime.now().isoformat(),
                'is_unread': True
            }]
        return []
    
    def create_action_file(self, message) -> Path:
        """
        Create action file in needs_action folder - HITL Entry Point
        
        Human-in-the-Loop Flow:
        1. Message detected -> Action file created in /needs_action
        2. Human reviews message in /needs_action
        3. If reply needed -> Create approval request in /pending_approval
        4. Human approves by moving file to /approved
        5. WhatsApp sender executes the reply
        """
        try:
            priority = self._determine_priority(message.get('matched_keywords', []))
            
            content = f"""---
type: whatsapp_message
from: {message.get('chat_name', 'Unknown Contact')}
received: {message.get('timestamp', datetime.now().isoformat())}
priority: {priority}
status: pending_review
matched_keywords: {', '.join(message.get('matched_keywords', []))}
is_unread: {message.get('is_unread', False)}
requires_approval: true
---

# WhatsApp Message Received ⚠️ REQUIRES HUMAN REVIEW

## Message Information
- **From**: {message.get('chat_name', 'Unknown Contact')}
- **Received**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Priority**: {priority}
- **Matched Keywords**: {', '.join(message.get('matched_keywords', []))}
- **Status**: {'Unread' if message.get('is_unread') else 'Read'}

## Message Content
{message.get('text', 'No content available')}

## ─────────────────────────────────────────────
## HUMAN-IN-THE-LOOP WORKFLOW
## ─────────────────────────────────────────────

### Step 1: Review This Message
- [ ] Read and understand the message
- [ ] Determine if response is needed

### Step 2: If Response Needed - Create Approval Request
Use the WhatsApp Sender skill to create an approval request:

```python
from watchers.whatsapp_watcher import WhatsAppWatcher
watcher = WhatsAppWatcher()
watcher.create_reply_approval_request(
    contact="{message.get('chat_name', 'Unknown Contact')}",
    reply_message="Your drafted response here",
    original_message="{message.get('text', '')[:50]}..."
)
```

Or manually create file in `/pending_approval/`:
```markdown
---
type: approval_request
action: whatsapp_reply
to: {message.get('chat_name', 'Unknown Contact')}
reply_message: [Your response]
---
```

### Step 3: Approve and Send
- Move approval file to `/approved/` to send
- Message will be sent via WhatsApp Sender skill
- Action logged in audit system

## ─────────────────────────────────────────────

## Notes
- Flagged for keywords: {', '.join(message.get('matched_keywords', []))}
- Priority: {priority} - {'⚠️ RESPOND IMMEDIATELY!' if priority == 'high' else 'Review during next check'}
- HITL: All WhatsApp actions require human approval
"""
            
            chat_name = message.get('chat_name', 'unknown').replace(' ', '_').replace('/', '_').replace(':', '_')
            filepath = self.needs_action / f'WHATSAPP_{chat_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f"✓ Action file created: {filepath}")
            
            # For high priority, also create notification in pending_approval
            if priority == 'high':
                self._create_priority_notification(filepath, message)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None
    
    def _create_priority_notification(self, action_file: Path, message: dict):
        """Create priority notification for high priority messages"""
        try:
            notification_file = self.pending_approval / f'PRIORITY_WHATSAPP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            
            content = f"""---
type: priority_notification
category: whatsapp_message
from: {message.get('chat_name', 'Unknown Contact')}
priority: high
created: {datetime.now().isoformat()}
status: requires_attention
---

# ⚠️ HIGH PRIORITY WhatsApp Message

## Immediate Attention Required

**From:** {message.get('chat_name', 'Unknown Contact')}  
**Keywords:** {', '.join(message.get('matched_keywords', []))}  
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Action Required

1. Review: `{action_file.name}` in /needs_action/
2. Draft response if needed
3. Create approval request to reply

---
*Auto-created by WhatsApp Watcher (HITL)*
"""
            
            notification_file.write_text(content, encoding='utf-8')
            self.logger.info(f"✓ Priority notification: {notification_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating priority notification: {e}")
    
    def create_reply_approval_request(self, contact: str, reply_message: str, 
                                       original_message: str = None) -> Path:
        """
        Create approval request for WhatsApp reply - HITL Enforcement Point
        
        NO WhatsApp messages can be sent without this approval file.
        This is the Human-in-the-Loop gate.
        
        Args:
            contact: Contact name or phone number
            reply_message: Message to send
            original_message: Original message being replied to
            
        Returns:
            Path to created approval file
        """
        try:
            self.pending_approval.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            approval_file = self.pending_approval / f'WHATSAPP_REPLY_{timestamp}.md'
            
            content = f"""---
type: approval_request
action: whatsapp_send
to: {contact}
reply_message: {reply_message[:200]}
created: {datetime.now().isoformat()}
status: pending
requires_human_approval: true
---

# WhatsApp Reply Approval ⚠️ HUMAN-IN-THE-LOOP

## Message Details
- **To**: {contact}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Reply Message
```
{reply_message}
```

{f"## Original Message\n```\n{original_message}\n```\n" if original_message else ""}

## ─────────────────────────────────────────────
## APPROVAL REQUIRED
## ─────────────────────────────────────────────

This message CANNOT be sent without your explicit approval.

### To APPROVE:
1. Review the message content
2. Verify recipient is correct
3. Move this file to `/approved/` folder
4. Orchestrator will execute the send

### To REJECT:
1. Move to `/rejected/` folder, OR
2. Delete this file

## Security
- All WhatsApp actions require human approval
- Action logged in audit system
- Sent via authenticated WhatsApp Web
"""
            
            approval_file.write_text(content, encoding='utf-8')
            self.logger.info(f"✓ Approval request created: {approval_file}")
            
            return approval_file
            
        except Exception as e:
            self.logger.error(f"Error creating approval request: {e}")
            return None
    
    def _determine_priority(self, matched_keywords: list) -> str:
        """Determine message priority"""
        high_priority = ['urgent', 'asap', 'emergency', 'help']
        medium_priority = ['invoice', 'payment', 'meeting', 'deadline']
        
        for kw in matched_keywords:
            if kw in high_priority:
                return 'high'
        for kw in matched_keywords:
            if kw in medium_priority:
                return 'medium'
        return 'normal'
    
    def run(self):
        """Start watching WhatsApp"""
        print("\n" + "=" * 60)
        print("WhatsApp Watcher - AI Employee Silver Tier")
        print("=" * 60)
        print(f"\n📁 Session: {self.session_path}")
        print(f"🔑 Keywords: {', '.join(self.keywords)}")
        print(f"⏱️  Interval: {self.check_interval}s")
        print(f"🎭 Demo: {self.demo_mode}")
        print(f"🔒 HITL: All messages require human review")
        print("\n" + "=" * 60)
        print("FIRST TIME SETUP:")
        print("1. Browser window will open")
        print("2. Scan QR code with WhatsApp on your phone")
        print("3. After auth, monitoring begins automatically")
        print("=" * 60 + "\n")
        
        self.logger.info('Starting WhatsAppWatcher')
        
        if not self.whatsapp_enabled:
            self.logger.warning("WhatsApp disabled in .env")
            return
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        self.create_action_file(item)
                    
                    if items:
                        self.logger.info(f"Processed {len(items)} messages")
                        
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
            print("\n\nStopping WhatsApp Watcher...")
        except Exception as e:
            self.logger.error(f"Error: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'context') and self.context:
                self.context.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
            self.logger.info("WhatsApp Watcher stopped")
        except:
            pass


def main():
    """Main entry point"""
    watcher = WhatsAppWatcher(str(project_root), check_interval=30)
    watcher.run()


if __name__ == "__main__":
    main()
