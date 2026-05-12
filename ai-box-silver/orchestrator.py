"""
Orchestrator for AI Employee Silver Tier
Coordinates watchers, Claude reasoning, and action execution
Creates Plan.md files for task tracking
"""
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import yaml

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class Orchestrator:
    """Main orchestrator for the AI Employee system"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else project_root
        self.needs_action = self.project_path / 'needs_action'
        self.plans = self.project_path / 'plans'
        self.pending_approval = self.project_path / 'pending_approval'
        self.approved = self.project_path / 'approved'
        self.done = self.project_path / 'done'
        self.logs = self.project_path / 'logs'
        self.inbox = self.project_path / 'inbox'
        
        # Create directories
        for folder in [self.needs_action, self.plans, self.pending_approval, 
                       self.approved, self.done, self.logs, self.inbox]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # State tracking
        self.processed_files = set()
        self.current_plan = None
        
        self.logger.info("Orchestrator initialized")
    
    def _setup_logging(self):
        """Setup logging for the orchestrator"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def check_needs_action(self) -> List[Path]:
        """Check for new files in needs_action folder"""
        new_files = []
        
        for file_path in self.needs_action.glob('*.md'):
            if str(file_path) not in self.processed_files:
                # Check if file is being processed (in plans folder)
                plan_exists = any(
                    p.name.startswith(f'PLAN_{file_path.stem}') 
                    for p in self.plans.glob('*.md')
                )
                
                if not plan_exists:
                    new_files.append(file_path)
                    self.processed_files.add(str(file_path))
        
        return new_files
    
    def create_plan(self, task_file: Path) -> Path:
        """Create a Plan.md file for a task"""
        try:
            # Read the task file
            content = task_file.read_text(encoding='utf-8')
            
            # Parse frontmatter
            metadata = self._parse_frontmatter(content)
            
            # Extract task type and details
            task_type = metadata.get('type', 'unknown')
            priority = metadata.get('priority', 'medium')
            from_field = metadata.get('from', metadata.get('original_name', 'Unknown'))
            
            # Create plan content
            plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: pending
priority: {priority}
task_type: {task_type}
source_file: {task_file.name}
objective: Process {task_type} from {from_field}
---

# Plan: {task_type.title()} Processing

## Objective
Process the {task_type} from {from_field} and take appropriate action.

## Context
- **Source**: {task_file.name}
- **Priority**: {priority}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Steps
- [ ] Read and analyze the {task_type} content
- [ ] Determine required actions
- [ ] Check if approval is needed
- [ ] Execute actions or create approval request
- [ ] Update dashboard
- [ ] Move to done folder

## Notes
Add any observations or decisions here during processing.

## Claude Reasoning
<!-- This section will be populated by Claude Code during processing -->

"""
            
            # Create plan file
            plan_filename = f'PLAN_{task_file.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            plan_path = self.plans / plan_filename
            plan_path.write_text(plan_content, encoding='utf-8')
            
            self.logger.info(f"Plan created: {plan_path}")
            self.current_plan = plan_path
            
            # Log the action
            self._log_action('plan_created', {
                'plan_file': str(plan_path),
                'task_file': str(task_file),
                'task_type': task_type
            })
            
            return plan_path
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            return None
    
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
                try:
                    metadata = yaml.safe_load(fm_content) or {}
                except:
                    # Fallback to simple parsing
                    for line in fm_content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
        
        return metadata
    
    def process_with_claude(self, plan_file: Path) -> bool:
        """
        Process a plan using Claude Code
        This invokes Claude to reason about the task and execute actions
        """
        try:
            self.logger.info(f"Processing plan with Claude: {plan_file}")
            
            # Read the plan
            plan_content = plan_file.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(plan_content)
            
            # Get task type and source file
            task_type = metadata.get('task_type', 'unknown')
            source_file = metadata.get('source_file', '')
            
            # Find the source file in needs_action
            source_path = self.needs_action / source_file
            if not source_path.exists():
                self.logger.warning(f"Source file not found: {source_path}")
                return False
            
            # Read the source task
            task_content = source_path.read_text(encoding='utf-8')
            
            # Create Claude prompt
            prompt = self._create_claude_prompt(task_type, task_content, plan_content)
            
            # Write prompt to a temporary file for Claude
            prompt_file = self.logs / f'claude_prompt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            prompt_file.write_text(prompt, encoding='utf-8')
            
            self.logger.info(f"Prompt created: {prompt_file}")
            
            # In a real implementation, this would invoke Claude Code
            # For now, we'll create a structured response
            return self._simulate_claude_processing(plan_file, source_path, task_type)
            
        except Exception as e:
            self.logger.error(f"Error processing with Claude: {e}")
            return False
    
    def _create_claude_prompt(self, task_type: str, task_content: str, plan_content: str) -> str:
        """Create a prompt for Claude Code"""
        return f"""You are an AI Employee assistant. Process the following task:

## Task Type: {task_type}

## Task Content:
{task_content}

## Current Plan:
{plan_content}

## Your Responsibilities:
1. Analyze the task content and understand what action is needed
2. Determine if this requires human approval (payments, sensitive communications)
3. If approval is needed, create an approval request file in /pending_approval
4. If no approval needed, execute the action using available MCP servers
5. Update the plan file with your reasoning and actions taken
6. Move the task to /done when complete

## Available Tools:
- File system access (read/write/move files)
- Email MCP server (send_email, draft_email)
- LinkedIn poster skill (post_to_linkedin, schedule_business_post)
- Dashboard update skill

## Company Rules:
- Always be professional in communications
- Flag payments over $100 for approval
- Flag new contacts for approval
- Log all actions taken
"""
    
    def _simulate_claude_processing(self, plan_file: Path, source_file: Path, task_type: str) -> bool:
        """Simulate Claude processing (in real implementation, this calls Claude Code API)"""
        try:
            # Read current plan
            plan_content = plan_file.read_text(encoding='utf-8')
            
            # Add reasoning section
            reasoning = f"""
## Claude Reasoning (Auto-generated)
- **Analysis Time**: {datetime.now().isoformat()}
- **Task Type**: {task_type}
- **Assessment**: Task analyzed and categorized
- **Action Required**: {'Approval needed' if self._requires_approval(task_type) else 'Can process automatically'}
"""
            
            # Update plan with reasoning
            if '<!-- This section will be populated by Claude Code during processing -->' in plan_content:
                plan_content = plan_content.replace(
                    '<!-- This section will be populated by Claude Code during processing -->',
                    reasoning
                )
                plan_file.write_text(plan_content, encoding='utf-8')
            
            # Check if approval is needed
            if self._requires_approval(task_type):
                self._create_approval_request(plan_file, source_file, task_type)
                self.logger.info("Approval request created")
            else:
                # Process automatically
                self._process_automatically(plan_file, source_file, task_type)
                self.logger.info("Task processed automatically")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Claude processing simulation: {e}")
            return False
    
    def _requires_approval(self, task_type: str) -> bool:
        """Determine if a task type requires human approval"""
        approval_required_types = [
            'email',  # All emails need approval in silver tier
            'payment',
            'invoice',
            'contract',
            'legal'
        ]
        
        return any(t in task_type.lower() for t in approval_required_types)
    
    def _create_approval_request(self, plan_file: Path, source_file: Path, task_type: str):
        """Create an approval request file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_file = self.pending_approval / f'APPROVAL_{task_type}_{timestamp}.md'
        
        content = f"""---
type: approval_request
action: {task_type}_processing
created: {datetime.now().isoformat()}
status: pending
source_plan: {plan_file.name}
source_task: {source_file.name}
---

# Approval Required: {task_type.title()} Processing

## Details
- **Task Type**: {task_type}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source Plan**: {plan_file.name}

## Why Approval is Needed
This action requires human approval because it involves {task_type} processing
which may have important business implications.

## To Approve
1. Review the linked plan file: {plan_file.name}
2. Review the source task: {source_file.name}
3. Move this file to the `/approved` folder to proceed

## To Reject
Move this file to the `/rejected` folder or delete it.

## Notes
- The AI Employee has paused execution pending your approval
- All actions will be logged for audit purposes
"""
        
        approval_file.write_text(content, encoding='utf-8')
        
        # Update plan status
        plan_content = plan_file.read_text(encoding='utf-8')
        plan_content = plan_content.replace('status: pending', 'status: awaiting_approval')
        plan_file.write_text(plan_content, encoding='utf-8')
        
        self._log_action('approval_requested', {
            'approval_file': str(approval_file),
            'task_type': task_type
        })
    
    def _process_automatically(self, plan_file: Path, source_file: Path, task_type: str):
        """Process a task automatically (no approval needed)"""
        try:
            # Update plan status
            plan_content = plan_file.read_text(encoding='utf-8')
            plan_content = plan_content.replace('status: pending', 'status: completed')
            plan_content += f"\n## Completed\n- **Completed at**: {datetime.now().isoformat()}\n"
            plan_file.write_text(plan_content, encoding='utf-8')
            
            # Move source file to done
            done_file = self.done / source_file.name
            source_file.rename(done_file)
            
            # Move plan to done
            done_plan = self.done / plan_file.name
            plan_file.rename(done_plan)
            
            self._log_action('task_completed', {
                'task_type': task_type,
                'source_file': str(source_file),
                'done_file': str(done_file)
            })
            
        except Exception as e:
            self.logger.error(f"Error processing task automatically: {e}")
    
    def check_approved_actions(self) -> List[Path]:
        """Check for approved actions to execute"""
        approved_files = list(self.approved.glob('*.md'))
        return approved_files
    
    def execute_approved_action(self, approval_file: Path) -> bool:
        """Execute an approved action"""
        try:
            content = approval_file.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(content)
            
            action_type = metadata.get('action', 'unknown')
            self.logger.info(f"Executing approved action: {action_type}")
            
            # Execute based on action type
            if 'linkedin' in action_type.lower():
                self._execute_linkedin_post(approval_file)
            elif 'email' in action_type.lower():
                self._execute_email_send(approval_file)
            else:
                self._execute_generic_action(approval_file)
            
            # Move to done
            done_file = self.done / approval_file.name
            approval_file.rename(done_file)
            
            self._log_action('approved_action_executed', {
                'action_type': action_type,
                'file': str(approval_file)
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing approved action: {e}")
            return False
    
    def _execute_linkedin_post(self, approval_file: Path):
        """Execute a LinkedIn post"""
        from skills.linkedin_poster import post_to_linkedin
        
        content = approval_file.read_text()
        # Extract post content (simplified - in reality would parse better)
        
        result = post_to_linkedin(
            content="Business update from AI Employee",
            title="Automated Post"
        )
        
        self.logger.info(f"LinkedIn post result: {result}")
    
    def _execute_email_send(self, approval_file: Path):
        """Execute an email send"""
        from mcp_servers.email_mcp import EmailMCPServer
        
        server = EmailMCPServer()
        # In reality, would parse recipient, subject, body from approval file
        
        self.logger.info("Email send executed (demo)")
    
    def _execute_generic_action(self, approval_file: Path):
        """Execute a generic approved action"""
        self.logger.info(f"Generic action executed: {approval_file.name}")
    
    def _log_action(self, action_type: str, details: dict):
        """Log an action for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "orchestrator",
            "details": details
        }
        
        log_file = self.logs / f'orchestrator_actions_{datetime.now().strftime("%Y%m%d")}.json'
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
    
    def run(self):
        """Main orchestration loop"""
        self.logger.info("Starting orchestrator main loop")
        
        try:
            while True:
                # Check for new tasks
                new_tasks = self.check_needs_action()
                
                for task_file in new_tasks:
                    self.logger.info(f"Processing new task: {task_file.name}")
                    
                    # Create a plan
                    plan_file = self.create_plan(task_file)
                    
                    if plan_file:
                        # Process with Claude
                        self.process_with_claude(plan_file)
                
                # Check for approved actions
                approved_actions = self.check_approved_actions()
                
                for approval_file in approved_actions:
                    self.logger.info(f"Executing approved action: {approval_file.name}")
                    self.execute_approved_action(approval_file)
                
                # Wait before next check
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("Orchestrator stopped by user")
        except Exception as e:
            self.logger.error(f"Error in orchestrator: {e}")
            raise


def main():
    """Main entry point"""
    print("Starting AI Employee Silver Tier Orchestrator...")
    
    orchestrator = Orchestrator(str(project_root))
    orchestrator.run()


if __name__ == "__main__":
    main()
