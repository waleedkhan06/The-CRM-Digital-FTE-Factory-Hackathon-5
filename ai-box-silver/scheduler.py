"""
Scheduler for AI Employee Silver Tier
Handles periodic operations like daily briefings, weekly audits, and scheduled posts
"""
import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
import schedule


# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TaskScheduler:
    """Scheduler for periodic AI Employee tasks"""
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = project_root
        else:
            self.project_path = Path(project_path)
        
        self.logs = self.project_path / 'logs'
        self.plans = self.project_path / 'plans'
        self.done = self.project_path / 'done'
        
        # Create directories
        self.logs.mkdir(parents=True, exist_ok=True)
        self.plans.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Scheduled jobs tracking
        self.jobs = []
        self.running = False
        self.scheduler_thread = None
        
        self.logger.info("TaskScheduler initialized")
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs / f'scheduler_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def setup_daily_tasks(self):
        """Setup daily recurring tasks"""
        # Daily briefing at 8:00 AM
        schedule.every().day.at("08:00").do(
            self.run_daily_briefing,
            name="daily_briefing_8am"
        )
        self.jobs.append("daily_briefing_8am")
        
        # End of day summary at 6:00 PM
        schedule.every().day.at("18:00").do(
            self.run_eod_summary,
            name="eod_summary_6pm"
        )
        self.jobs.append("eod_summary_6pm")
        
        # Cleanup expired approvals at midnight
        schedule.every().day.at("00:00").do(
            self.cleanup_expired_approvals,
            name="cleanup_midnight"
        )
        self.jobs.append("cleanup_midnight")
        
        self.logger.info("Daily tasks scheduled")
    
    def setup_weekly_tasks(self):
        """Setup weekly recurring tasks"""
        # Weekly audit every Monday at 7:00 AM
        schedule.every().monday.at("07:00").do(
            self.run_weekly_audit,
            name="weekly_audit_monday"
        )
        self.jobs.append("weekly_audit_monday")
        
        # LinkedIn business post every Wednesday at 9:00 AM
        schedule.every().wednesday.at("09:00").do(
            self.run_linkedin_post,
            name="linkedin_post_wednesday"
        )
        self.jobs.append("linkedin_post_wednesday")
        
        # Friday status report at 4:00 PM
        schedule.every().friday.at("16:00").do(
            self.run_friday_report,
            name="friday_report_4pm"
        )
        self.jobs.append("friday_report_4pm")
        
        self.logger.info("Weekly tasks scheduled")
    
    def run_daily_briefing(self, name: str = "daily_briefing"):
        """Generate daily briefing for the user"""
        self.logger.info(f"Running {name}")
        
        try:
            # Count tasks in each folder
            needs_action_count = len(list((self.project_path / 'needs_action').glob('*.md')))
            pending_approval_count = len(list((self.project_path / 'pending_approval').glob('*.md')))
            plans_count = len(list(self.plans.glob('*.md')))
            
            # Create briefing file
            briefing_content = f"""---
type: daily_briefing
date: {datetime.now().strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# Daily Briefing - {datetime.now().strftime('%A, %B %d, %Y')}

## Overview
Good morning! Here's your daily AI Employee briefing.

## Current Status
- **Tasks Needing Action**: {needs_action_count}
- **Pending Approval**: {pending_approval_count}
- **Active Plans**: {plans_count}

## Priority Items
"""
            
            # List high priority items
            needs_action = self.project_path / 'needs_action'
            high_priority_items = []
            
            for file_path in needs_action.glob('*.md'):
                content = file_path.read_text()
                if 'priority: high' in content.lower():
                    high_priority_items.append(file_path.name)
            
            if high_priority_items:
                briefing_content += "\n### High Priority Tasks\n"
                for item in high_priority_items[:5]:
                    briefing_content += f"- {item}\n"
            else:
                briefing_content += "\nNo high priority items at this time.\n"
            
            briefing_content += f"""

## Today's Goals
- [ ] Review and process pending tasks
- [ ] Approve or reject pending requests
- [ ] Check completed items in /done

## Notes
Generated automatically by AI Employee Scheduler.

---
*Have a productive day!*
"""
            
            # Save briefing
            briefing_file = self.plans / f'BRIEFING_{datetime.now().strftime("%Y%m%d")}.md'
            briefing_file.write_text(briefing_content, encoding='utf-8')
            
            self._log_task_execution(name, {
                'briefing_file': str(briefing_file),
                'needs_action_count': needs_action_count,
                'pending_approval_count': pending_approval_count
            })
            
            self.logger.info(f"Daily briefing created: {briefing_file}")
            
        except Exception as e:
            self.logger.error(f"Error in daily briefing: {e}")
    
    def run_eod_summary(self, name: str = "eod_summary"):
        """Generate end of day summary"""
        self.logger.info(f"Running {name}")
        
        try:
            # Count completed items today
            done_folder = self.project_path / 'done'
            today_count = 0
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            for file_path in done_folder.glob('*.md'):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime.strftime('%Y-%m-%d') == today_str:
                    today_count += 1
            
            summary_content = f"""---
type: eod_summary
date: {datetime.now().strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# End of Day Summary - {datetime.now().strftime('%A, %B %d, %Y')}

## Today's Accomplishments
- **Tasks Completed**: {today_count}

## Summary
Another productive day completed! The AI Employee has processed {today_count} items today.

## Tomorrow's Preview
Check your daily briefing at 8:00 AM for tomorrow's priorities.

---
*Rest well! Your AI Employee continues monitoring overnight.*
"""
            
            summary_file = self.done / f'EOD_SUMMARY_{datetime.now().strftime("%Y%m%d")}.md'
            summary_file.write_text(summary_content, encoding='utf-8')
            
            self._log_task_execution(name, {
                'summary_file': str(summary_file),
                'completed_count': today_count
            })
            
            self.logger.info(f"EOD summary created: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error in EOD summary: {e}")
    
    def run_weekly_audit(self, name: str = "weekly_audit"):
        """Run weekly business audit"""
        self.logger.info(f"Running {name}")
        
        try:
            # This would integrate with accounting system in Gold tier
            # For Silver tier, create a basic audit report
            
            audit_content = f"""---
type: weekly_audit
week_start: {(datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')}
week_end: {(datetime.now() + timedelta(days=6-datetime.now().weekday())).strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# Weekly Business Audit

## Week of {datetime.now().strftime('%B %d, %Y')}

## Activity Summary

### Tasks Processed
- Count tasks completed this week from /done folder

### Pending Items
- Review items in /needs_action
- Review items in /pending_approval

## CEO Briefing Notes

### Revenue Tracking
<!-- In Gold tier, this would integrate with Odoo/banking APIs -->
- Manual review of transactions required

### Bottlenecks Identified
<!-- Items that took longer than expected -->
- Review plan files for delayed items

### Cost Optimization
<!-- Subscription audit, unused services -->
- Review recurring expenses

## Action Items for This Week
- [ ] Review all pending approvals
- [ ] Process backlog in needs_action
- [ ] Update business goals if needed
- [ ] Schedule any delayed tasks

---
*Generated by AI Employee - Weekly Audit System*
"""
            
            audit_file = self.plans / f'WEEKLY_AUDIT_{datetime.now().strftime("%Y%m%d")}.md'
            audit_file.write_text(audit_content, encoding='utf-8')
            
            self._log_task_execution(name, {
                'audit_file': str(audit_file)
            })
            
            self.logger.info(f"Weekly audit created: {audit_file}")
            
        except Exception as e:
            self.logger.error(f"Error in weekly audit: {e}")
    
    def run_linkedin_post(self, name: str = "linkedin_post"):
        """Schedule/create LinkedIn business post"""
        self.logger.info(f"Running {name}")
        
        try:
            from skills.linkedin_poster import schedule_business_post, create_approval_request
            
            # Generate business post content
            post_result = schedule_business_post(
                topic="Weekly Business Update",
                include_hashtags=True
            )
            
            if post_result['status'] == 'success':
                # Create approval request
                approval_result = create_approval_request(
                    content=post_result['content'],
                    scheduled_time=datetime.now().strftime('%Y-%m-%d %H:%M')
                )
                
                self._log_task_execution(name, {
                    'post_result': post_result,
                    'approval_result': approval_result
                })
                
                self.logger.info(f"LinkedIn post created for approval")
            
        except Exception as e:
            self.logger.error(f"Error in LinkedIn post: {e}")
    
    def run_friday_report(self, name: str = "friday_report"):
        """Generate Friday status report"""
        self.logger.info(f"Running {name}")
        
        try:
            # Count week's activity
            done_folder = self.project_path / 'done'
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            
            week_count = 0
            for file_path in done_folder.glob('*.md'):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime >= week_start:
                    week_count += 1
            
            report_content = f"""---
type: friday_report
week_ending: {datetime.now().strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# Friday Status Report

## Week Ending {datetime.now().strftime('%B %d, %Y')}

## Weekly Summary
- **Total Tasks Completed**: {week_count}
- **Average per Day**: {week_count / 5:.1f}

## This Week's Highlights
<!-- Add notable accomplishments here -->

## Pending for Next Week
<!-- Items carried over -->

## Weekend Notes
- AI Employee will continue monitoring over the weekend
- Urgent items will be flagged for attention
- Regular operations resume Monday 8:00 AM

---
*Have a great weekend!*
"""
            
            report_file = self.done / f'FRIDAY_REPORT_{datetime.now().strftime("%Y%m%d")}.md'
            report_file.write_text(report_content, encoding='utf-8')
            
            self._log_task_execution(name, {
                'report_file': str(report_file),
                'week_count': week_count
            })
            
            self.logger.info(f"Friday report created: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error in Friday report: {e}")
    
    def cleanup_expired_approvals(self, name: str = "cleanup"):
        """Clean up expired approval requests"""
        self.logger.info(f"Running {name}")
        
        try:
            from skills.approval_workflow import ApprovalWorkflow
            
            workflow = ApprovalWorkflow(str(self.project_path))
            result = workflow.cleanup_expired()
            
            self._log_task_execution(name, result)
            self.logger.info(f"Cleanup completed: {result.get('cleaned_count', 0)} items")
            
        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")
    
    def _log_task_execution(self, task_name: str, details: dict):
        """Log task execution"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_name": task_name,
            "actor": "scheduler",
            "details": details
        }
        
        log_file = self.logs / f'scheduler_tasks_{datetime.now().strftime("%Y%m%d")}.json'
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        self.logger.info("Starting scheduler loop")
        self.running = True
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
    
    def start(self):
        """Start the scheduler in a background thread"""
        # Setup all scheduled tasks
        self.setup_daily_tasks()
        self.setup_weekly_tasks()
        
        # Start scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started in background thread")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("Scheduler stopped")
    
    def get_scheduled_jobs(self) -> Dict:
        """Get list of scheduled jobs"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'name': getattr(job, 'name', 'unknown'),
                'next_run': str(job.next_run) if job.next_run else None
            })
        
        return {
            "status": "success",
            "jobs": jobs,
            "count": len(jobs),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point for scheduler"""
    print("Starting AI Employee Task Scheduler...")
    
    scheduler = TaskScheduler(str(project_root))
    scheduler.start()
    
    print("Scheduler running. Press Ctrl+C to stop.")
    print(f"Scheduled jobs: {scheduler.get_scheduled_jobs()}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()


if __name__ == "__main__":
    main()
