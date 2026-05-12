"""
WhatsApp Session Manager
Handles persistent authentication so you don't have to re-authenticate every time
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta


class WhatsAppSessionManager:
    """
    Manages WhatsApp Web session persistence.
    Authenticate once, use forever (until WhatsApp logs you out).
    """
    
    def __init__(self, session_path: str):
        self.session_path = Path(session_path)
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.session_path / 'session_state.json'
        self.cookies_file = self.session_path / 'whatsapp_cookies.json'
        
        self.session_data = self._load_state()
    
    def _load_state(self) -> dict:
        """Load session state from file"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            'authenticated': False,
            'last_auth': None,
            'expires': None,
            'phone': None
        }
    
    def _save_state(self):
        """Save session state to file"""
        self.state_file.write_text(json.dumps(self.session_data, indent=2))
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid session"""
        # Check if cookies file exists
        if not self.cookies_file.exists():
            return False
        
        # Check state
        if not self.session_data.get('authenticated'):
            return False
        
        # Check if expired (WhatsApp sessions last ~30 days)
        expires = self.session_data.get('expires')
        if expires:
            try:
                expiry = datetime.fromisoformat(expires)
                if datetime.now() > expiry:
                    self.session_data['authenticated'] = False
                    self._save_state()
                    return False
            except:
                pass
        
        return True
    
    def mark_authenticated(self, phone: str = None):
        """Mark session as authenticated"""
        self.session_data.update({
            'authenticated': True,
            'last_auth': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=30)).isoformat(),
            'phone': phone
        })
        self._save_state()
    
    def save_cookies(self, cookies: list):
        """Save cookies to file"""
        self.cookies_file.write_text(json.dumps(cookies, indent=2))
    
    def load_cookies(self) -> list:
        """Load cookies from file"""
        if self.cookies_file.exists():
            try:
                return json.loads(self.cookies_file.read_text())
            except:
                pass
        return []
    
    def clear_session(self):
        """Clear all session data"""
        self.state_file.unlink(missing_ok=True)
        self.cookies_file.unlink(missing_ok=True)
        self.session_data = {
            'authenticated': False,
            'last_auth': None,
            'expires': None,
            'phone': None
        }
    
    def get_status(self) -> dict:
        """Get session status"""
        return {
            'authenticated': self.is_authenticated(),
            'last_auth': self.session_data.get('last_auth'),
            'expires': self.session_data.get('expires'),
            'phone': self.session_data.get('phone'),
            'session_path': str(self.session_path)
        }


# Test
if __name__ == '__main__':
    session = WhatsAppSessionManager('/tmp/test_whatsapp')
    print(session.get_status())
