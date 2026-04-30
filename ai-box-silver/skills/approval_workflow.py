"""
Agent Skill: Approval Workflow
Human-in-the-loop approval management for sensitive actions
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class ApprovalWorkflow:
    """Manages human-in-the-loop approval workflow"""
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(__file__).parent.parent
        else:
            self.project_path = Path(project_path)
        
        self.pending_approval = self.project_path / 'pending_approval'
        self.approved = self.project_path / 'approved'
        self.rejected = self.project_path / 'rejected'
        self.done = self.project_path / 'done'
        self.logs = self.project_path / 'logs'
        
        # Create directories
        for folder in [self.pending_approval, self.approved, self.rejected, 
                       self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
    
    def create_approval_request(self, action_type: str, details: dict, 
                                reason: str = None) -> Dict:
        """
        Create an approval request file
        
        Args:
            action_type (str): Type of action requiring approval
            details (dict): Details about the action
            reason (str): Reason why approval is needed
            
        Returns:
            dict: Result with approval request file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_action = action_type.replace(' ', '_').lower()
        approval_file = self.pending_approval / f'APPROVAL_{safe_action}_{timestamp}.md'
        
        # Build details section
        details_md = "\n".join([f"- **{k.replace('_', ' ').title()}**: {v}" 
                                for k, v in details.items()])
        
        content = f"""---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
status: pending
priority: {details.get('priority', 'medium')}
expires: {(datetime.now().replace(hour=23, minute=59)).isoformat()}
---

# Approval Required: {action_type.replace('_', ' ').title()}

## Details
{details_md}

## Reason for Approval
{reason or 'This action requires human review before proceeding.'}

## To Approve
Move this file to the `/approved` folder to proceed with this action.

## To Reject
Move this file to the `/rejected` folder or delete it.

## Notes
- Approval requests expire at end of day
- All actions are logged for audit purposes
- Contact administrator if you have questions
"""
        
        approval_file.write_text(content, encoding='utf-8')
        
        self._log_action('approval_request_created', {
            'file': str(approval_file),
            'action_type': action_type
        })
        
        return {
            "status": "success",
            "message": f"Approval request created",
            "approval_file": str(approval_file),
            "action_type": action_type,
            "timestamp": datetime.now().isoformat()
        }
    
    def approve_request(self, approval_file_path: str) -> Dict:
        """
        Approve a request by moving it to the approved folder
        
        Args:
            approval_file_path (str): Path to the approval request file
            
        Returns:
            dict: Result of the approval
        """
        source = Path(approval_file_path)
        
        if not source.exists():
            return {
                "status": "error",
                "message": f"Approval file not found: {approval_file_path}",
                "timestamp": datetime.now().isoformat()
            }
        
        if source.parent != self.pending_approval:
            return {
                "status": "error",
                "message": "File must be in pending_approval folder",
                "timestamp": datetime.now().isoformat()
            }
        
        dest = self.approved / source.name
        
        # Handle if file already exists in approved
        if dest.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = self.approved / f"{source.stem}_{timestamp}{source.suffix}"
        
        shutil.move(str(source), str(dest))
        
        # Update the file content to show approval
        content = dest.read_text(encoding='utf-8')
        content = content.replace('status: pending', 'status: approved')
        content += f"\n## Approved\n- **Approved at**: {datetime.now().isoformat()}\n"
        dest.write_text(content, encoding='utf-8')
        
        self._log_action('approval_granted', {
            'file': str(dest),
            'action_type': self._extract_action_type(content)
        })
        
        return {
            "status": "success",
            "message": f"Request approved: {source.name}",
            "approved_file": str(dest),
            "timestamp": datetime.now().isoformat()
        }
    
    def reject_request(self, approval_file_path: str, reason: str = None) -> Dict:
        """
        Reject a request by moving it to the rejected folder
        
        Args:
            approval_file_path (str): Path to the approval request file
            reason (str): Reason for rejection
            
        Returns:
            dict: Result of the rejection
        """
        source = Path(approval_file_path)
        
        if not source.exists():
            return {
                "status": "error",
                "message": f"Approval file not found: {approval_file_path}",
                "timestamp": datetime.now().isoformat()
            }
        
        if source.parent != self.pending_approval:
            return {
                "status": "error",
                "message": "File must be in pending_approval folder",
                "timestamp": datetime.now().isoformat()
            }
        
        dest = self.rejected / source.name
        
        # Handle if file already exists in rejected
        if dest.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = self.rejected / f"{source.stem}_{timestamp}{source.suffix}"
        
        shutil.move(str(source), str(dest))
        
        # Update the file content to show rejection
        content = dest.read_text(encoding='utf-8')
        content = content.replace('status: pending', 'status: rejected')
        content += f"\n## Rejected\n- **Rejected at**: {datetime.now().isoformat()}\n"
        if reason:
            content += f"- **Reason**: {reason}\n"
        dest.write_text(content, encoding='utf-8')
        
        self._log_action('approval_rejected', {
            'file': str(dest),
            'reason': reason or 'Not specified'
        })
        
        return {
            "status": "success",
            "message": f"Request rejected: {source.name}",
            "rejected_file": str(dest),
            "timestamp": datetime.now().isoformat()
        }
    
    def list_pending_requests(self) -> Dict:
        """
        List all pending approval requests
        
        Returns:
            dict: List of pending requests
        """
        requests = []
        
        for file_path in self.pending_approval.glob('*.md'):
            content = file_path.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(content)
            
            requests.append({
                'filename': file_path.name,
                'path': str(file_path),
                'action_type': metadata.get('action', 'unknown'),
                'priority': metadata.get('priority', 'medium'),
                'created': metadata.get('created', 'unknown'),
                'size': file_path.stat().st_size
            })
        
        # Sort by priority and created time
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        requests.sort(key=lambda x: (
            priority_order.get(x['priority'], 1),
            x['created']
        ))
        
        return {
            "status": "success",
            "count": len(requests),
            "requests": requests,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_request_details(self, approval_file_path: str) -> Dict:
        """
        Get detailed information about an approval request
        
        Args:
            approval_file_path (str): Path to the approval request file
            
        Returns:
            dict: Request details
        """
        file_path = Path(approval_file_path)
        
        if not file_path.exists():
            return {
                "status": "error",
                "message": f"File not found: {approval_file_path}",
                "timestamp": datetime.now().isoformat()
            }
        
        content = file_path.read_text(encoding='utf-8')
        metadata = self._parse_frontmatter(content)
        
        return {
            "status": "success",
            "filename": file_path.name,
            "path": str(file_path),
            "metadata": metadata,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from markdown content"""
        metadata = {}
        lines = content.split('\n')
        
        if lines and lines[0].strip() == '---':
            end_fm_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_fm_idx = i
                    break
            
            if end_fm_idx > 0:
                fm_content = '\n'.join(lines[1:end_fm_idx])
                for line in fm_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
        
        return metadata
    
    def _extract_action_type(self, content: str) -> str:
        """Extract action type from content"""
        metadata = self._parse_frontmatter(content)
        return metadata.get('action', 'unknown')
    
    def _log_action(self, action_type: str, details: dict):
        """Log an action for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "approval_workflow",
            "details": details
        }
        
        log_file = self.logs / f'approval_workflow_{datetime.now().strftime("%Y%m%d")}.json'
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
    
    def cleanup_expired(self) -> Dict:
        """
        Clean up expired approval requests
        
        Returns:
            dict: Cleanup results
        """
        cleaned = []
        now = datetime.now()
        
        for file_path in self.pending_approval.glob('*.md'):
            content = file_path.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(content)
            
            expires = metadata.get('expires')
            if expires:
                try:
                    expiry_time = datetime.fromisoformat(expires)
                    if now > expiry_time:
                        # Move to rejected as expired
                        dest = self.rejected / f"expired_{file_path.name}"
                        shutil.move(str(file_path), str(dest))
                        cleaned.append(file_path.name)
                        self._log_action('approval_expired', {
                            'file': str(file_path)
                        })
                except:
                    pass
        
        return {
            "status": "success",
            "cleaned_count": len(cleaned),
            "cleaned_files": cleaned,
            "timestamp": datetime.now().isoformat()
        }


# Convenience functions for direct use
def create_approval_request(action_type: str, details: dict, 
                           reason: str = None, project_path: str = None) -> Dict:
    """Create an approval request"""
    workflow = ApprovalWorkflow(project_path)
    return workflow.create_approval_request(action_type, details, reason)


def approve_request(approval_file_path: str, project_path: str = None) -> Dict:
    """Approve a request"""
    workflow = ApprovalWorkflow(project_path)
    return workflow.approve_request(approval_file_path)


def reject_request(approval_file_path: str, reason: str = None, 
                   project_path: str = None) -> Dict:
    """Reject a request"""
    workflow = ApprovalWorkflow(project_path)
    return workflow.reject_request(approval_file_path, reason)


def list_pending_requests(project_path: str = None) -> Dict:
    """List pending requests"""
    workflow = ApprovalWorkflow(project_path)
    return workflow.list_pending_requests()


# Example usage
def run_example():
    """Example of how to use the approval workflow"""
    print("=== Approval Workflow Demo ===\n")
    
    workflow = ApprovalWorkflow()
    
    # Create an approval request
    print("Creating approval request...")
    result = workflow.create_approval_request(
        action_type="email_send",
        details={
            "to": "client@example.com",
            "subject": "Invoice #1234",
            "amount": "$500.00"
        },
        reason="Payment-related email requires approval"
    )
    print(json.dumps(result, indent=2))
    
    # List pending requests
    print("\nListing pending requests...")
    result = workflow.list_pending_requests()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run_example()
