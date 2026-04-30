"""
Audit Logging System for AI Employee Silver Tier
Comprehensive logging for all AI Employee actions with retention and query capabilities
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import hashlib


# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@dataclass
class AuditEntry:
    """Represents a single audit log entry"""
    timestamp: str
    action_type: str
    actor: str
    target: Optional[str] = None
    parameters: Optional[Dict] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    result: str = "unknown"
    error: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Comprehensive audit logging system
    
    Features:
    - Daily log files with automatic rotation
    - Structured JSON logging
    - Query and filter capabilities
    - Retention policy enforcement
    - Tamper-evident logging with hashes
    """
    
    # Action categories
    CATEGORY_PERCEPTION = "perception"  # Watchers detecting events
    CATEGORY_REASONING = "reasoning"    # Claude processing
    CATEGORY_ACTION = "action"          # Executing actions
    CATEGORY_APPROVAL = "approval"      # Approval workflow
    CATEGORY_SYSTEM = "system"          # System events
    
    def __init__(self, project_path: str = None, retention_days: int = 90):
        if project_path is None:
            self.project_path = project_root
        else:
            self.project_path = Path(project_path)
        
        self.logs_dir = self.project_path / 'logs' / 'audit'
        self.retention_days = retention_days
        
        # Create directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_id = self._generate_session_id()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Log file cache
        self._log_cache = {}
        
        # Setup standard logging
        self._setup_logging()
        
        self.logger.info(f"AuditLogger initialized with session {self.session_id}")
    
    def _setup_logging(self):
        """Setup Python logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.project_path / 'logs' / f'audit_system_{self.current_date}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return hashlib.md5(
            f"{datetime.now().isoformat()}{os.getpid()}".encode()
        ).hexdigest()[:12]
    
    def _get_log_file(self, date: str = None) -> Path:
        """Get the log file path for a given date"""
        if date is None:
            date = self.current_date
        
        return self.logs_dir / f'audit_{date}.jsonl'
    
    def log(self, action_type: str, actor: str, 
            target: str = None, parameters: dict = None,
            approval_status: str = None, approved_by: str = None,
            result: str = "success", error: str = None,
            category: str = None) -> AuditEntry:
        """
        Log an action to the audit system
        
        Args:
            action_type: Type of action (e.g., 'email_send', 'file_move')
            actor: Who/what performed the action (e.g., 'claude_code', 'gmail_watcher')
            target: What the action was performed on
            parameters: Additional parameters of the action
            approval_status: Status of approval if required
            approved_by: Who approved the action if applicable
            result: Result of the action (success, failed, pending)
            error: Error message if failed
            category: Optional category override
            
        Returns:
            AuditEntry: The created audit entry
        """
        # Determine category if not provided
        if category is None:
            category = self._infer_category(action_type)
        
        # Create the audit entry
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            actor=actor,
            target=target,
            parameters=parameters,
            approval_status=approval_status,
            approved_by=approved_by,
            result=result,
            error=error,
            session_id=self.session_id
        )
        
        # Write to log file
        self._write_entry(entry, category)
        
        # Also log to standard logger for immediate visibility
        log_level = logging.ERROR if result == "failed" else logging.INFO
        self.logger.log(
            log_level,
            f"[{category}] {action_type} by {actor}: {result}"
            + (f" - {error}" if error else "")
        )
        
        return entry
    
    def _infer_category(self, action_type: str) -> str:
        """Infer the category from action type"""
        action_lower = action_type.lower()
        
        if any(x in action_lower for x in ['watch', 'detect', 'monitor', 'check']):
            return self.CATEGORY_PERCEPTION
        elif any(x in action_lower for x in ['plan', 'reason', 'analyze', 'think']):
            return self.CATEGORY_REASONING
        elif any(x in action_lower for x in ['send', 'post', 'create', 'move', 'delete', 'execute']):
            return self.CATEGORY_ACTION
        elif any(x in action_lower for x in ['approve', 'reject', 'pending', 'approval']):
            return self.CATEGORY_APPROVAL
        else:
            return self.CATEGORY_SYSTEM
    
    def _write_entry(self, entry: AuditEntry, category: str):
        """Write an entry to the appropriate log file"""
        log_file = self._get_log_file()
        
        # Create entry with category
        log_entry = entry.to_dict()
        log_entry['category'] = category
        
        # Add hash for tamper evidence
        log_entry['hash'] = self._compute_hash(log_entry)
        
        # Append to JSONL file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Invalidate cache for this date
        if self.current_date in self._log_cache:
            del self._log_cache[self.current_date]
    
    def _compute_hash(self, entry: dict) -> str:
        """Compute a hash for tamper evidence"""
        # Hash all fields except the hash itself
        data = {k: v for k, v in entry.items() if k != 'hash'}
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def query(self, 
              start_date: str = None,
              end_date: str = None,
              action_type: str = None,
              actor: str = None,
              category: str = None,
              result: str = None,
              approval_status: str = None,
              limit: int = 100) -> List[Dict]:
        """
        Query audit logs with filters
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            action_type: Filter by action type
            actor: Filter by actor
            category: Filter by category
            result: Filter by result
            approval_status: Filter by approval status
            limit: Maximum results to return
            
        Returns:
            List of matching audit entries
        """
        results = []
        
        # Determine date range
        if start_date is None:
            start_date = self.current_date
        if end_date is None:
            end_date = self.current_date
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Iterate through date range
        current = start
        while current <= end and len(results) < limit:
            date_str = current.strftime('%Y-%m-%d')
            log_file = self._get_log_file(date_str)
            
            if log_file.exists():
                entries = self._read_log_file(log_file)
                
                for entry in entries:
                    if self._matches_filter(entry, action_type, actor, 
                                           category, result, approval_status):
                        results.append(entry)
                        
                        if len(results) >= limit:
                            break
            
            current += timedelta(days=1)
        
        return results
    
    def _read_log_file(self, log_file: Path) -> List[Dict]:
        """Read all entries from a log file"""
        date_str = log_file.stem.replace('audit_', '')
        
        # Check cache
        if date_str in self._log_cache:
            return self._log_cache[date_str]
        
        entries = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in log file: {log_file}")
        
        # Cache the entries
        self._log_cache[date_str] = entries
        
        return entries
    
    def _matches_filter(self, entry: dict, action_type: str, actor: str,
                        category: str, result: str, approval_status: str) -> bool:
        """Check if an entry matches the filter criteria"""
        if action_type and entry.get('action_type') != action_type:
            return False
        if actor and entry.get('actor') != actor:
            return False
        if category and entry.get('category') != category:
            return False
        if result and entry.get('result') != result:
            return False
        if approval_status and entry.get('approval_status') != approval_status:
            return False
        return True
    
    def get_summary(self, date: str = None) -> Dict:
        """
        Get a summary of audit logs for a date
        
        Args:
            date: Date to summarize (YYYY-MM-DD), defaults to today
            
        Returns:
            Summary statistics
        """
        if date is None:
            date = self.current_date
        
        log_file = self._get_log_file(date)
        
        if not log_file.exists():
            return {
                "status": "no_data",
                "date": date,
                "message": "No audit logs for this date"
            }
        
        entries = self._read_log_file(log_file)
        
        # Calculate statistics
        total = len(entries)
        by_category = {}
        by_result = {}
        by_actor = {}
        errors = []
        
        for entry in entries:
            # By category
            cat = entry.get('category', 'unknown')
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # By result
            result = entry.get('result', 'unknown')
            by_result[result] = by_result.get(result, 0) + 1
            
            # By actor
            actor = entry.get('actor', 'unknown')
            by_actor[actor] = by_actor.get(actor, 0) + 1
            
            # Collect errors
            if entry.get('error'):
                errors.append({
                    'timestamp': entry.get('timestamp'),
                    'action_type': entry.get('action_type'),
                    'error': entry.get('error')
                })
        
        return {
            "status": "success",
            "date": date,
            "total_entries": total,
            "by_category": by_category,
            "by_result": by_result,
            "by_actor": by_actor,
            "error_count": len(errors),
            "errors": errors[:10],  # Limit to first 10 errors
            "session_id": self.session_id
        }
    
    def enforce_retention(self) -> Dict:
        """
        Remove audit logs older than retention period
        
        Returns:
            Result of the cleanup operation
        """
        removed = []
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        for log_file in self.logs_dir.glob('audit_*.jsonl'):
            # Extract date from filename
            try:
                date_str = log_file.stem.replace('audit_', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff:
                    log_file.unlink()
                    removed.append(str(log_file))
                    self.logger.info(f"Removed old audit log: {log_file}")
            except ValueError:
                self.logger.warning(f"Invalid audit log filename: {log_file}")
        
        return {
            "status": "success",
            "removed_count": len(removed),
            "removed_files": removed,
            "retention_days": self.retention_days,
            "timestamp": datetime.now().isoformat()
        }
    
    def verify_integrity(self, date: str = None) -> Dict:
        """
        Verify the integrity of audit logs
        
        Args:
            date: Date to verify, defaults to today
            
        Returns:
            Verification results
        """
        if date is None:
            date = self.current_date
        
        log_file = self._get_log_file(date)
        
        if not log_file.exists():
            return {
                "status": "no_data",
                "message": f"No audit log for {date}"
            }
        
        entries = self._read_log_file(log_file)
        valid = 0
        invalid = 0
        
        for entry in entries:
            stored_hash = entry.pop('hash', None)
            computed_hash = self._compute_hash(entry)
            
            if stored_hash == computed_hash:
                valid += 1
            else:
                invalid += 1
                self.logger.warning(f"Hash mismatch in audit log: {entry.get('timestamp')}")
        
        return {
            "status": "verified" if invalid == 0 else "tampered",
            "date": date,
            "valid_entries": valid,
            "invalid_entries": invalid,
            "total_entries": valid + invalid,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_logs(self, output_path: str, 
                    start_date: str = None,
                    end_date: str = None,
                    format: str = 'json') -> Dict:
        """
        Export audit logs to a file
        
        Args:
            output_path: Path to export file
            start_date: Start date for export
            end_date: End date for export
            format: Export format ('json' or 'csv')
            
        Returns:
            Export result
        """
        entries = self.query(start_date=start_date, end_date=end_date, limit=10000)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2)
        elif format == 'csv':
            import csv
            if entries:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                    writer.writeheader()
                    writer.writerows(entries)
        else:
            return {
                "status": "error",
                "message": f"Unsupported format: {format}"
            }
        
        return {
            "status": "success",
            "exported_count": len(entries),
            "output_file": str(output_file),
            "format": format,
            "timestamp": datetime.now().isoformat()
        }


# Global audit logger instance
_audit_logger = None


def get_audit_logger(project_path: str = None) -> AuditLogger:
    """Get or create the global audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(project_path)
    return _audit_logger


# Convenience functions
def log_action(action_type: str, actor: str, **kwargs) -> AuditEntry:
    """Log an action using the global logger"""
    return get_audit_logger().log(action_type, actor, **kwargs)


def query_audit_logs(**kwargs) -> List[Dict]:
    """Query audit logs using the global logger"""
    return get_audit_logger().query(**kwargs)


# Example usage
def run_example():
    """Example of how to use the audit logging system"""
    print("=== Audit Logging System Demo ===\n")
    
    logger = AuditLogger(str(project_root))
    
    # Log some actions
    print("Logging actions...")
    
    logger.log(
        action_type="email_send",
        actor="email_mcp",
        target="client@example.com",
        parameters={"subject": "Invoice #1234"},
        approval_status="approved",
        approved_by="human",
        result="success",
        category=AuditLogger.CATEGORY_ACTION
    )
    
    logger.log(
        action_type="file_detected",
        actor="gmail_watcher",
        target="inbox",
        result="success",
        category=AuditLogger.CATEGORY_PERCEPTION
    )
    
    logger.log(
        action_type="plan_created",
        actor="orchestrator",
        target="PLAN_001.md",
        result="success",
        category=AuditLogger.CATEGORY_REASONING
    )
    
    logger.log(
        action_type="approval_requested",
        actor="approval_workflow",
        target="APPROVAL_001.md",
        approval_status="pending",
        result="success",
        category=AuditLogger.CATEGORY_APPROVAL
    )
    
    # Get summary
    print("\nToday's summary:")
    summary = logger.get_summary()
    print(json.dumps(summary, indent=2))
    
    # Query logs
    print("\nQuerying action logs:")
    results = logger.query(category=AuditLogger.CATEGORY_ACTION)
    print(json.dumps(results, indent=2))
    
    # Verify integrity
    print("\nVerifying integrity:")
    integrity = logger.verify_integrity()
    print(json.dumps(integrity, indent=2))


if __name__ == "__main__":
    run_example()
