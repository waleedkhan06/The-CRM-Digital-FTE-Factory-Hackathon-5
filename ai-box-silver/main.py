"""
Main script to run the AI Employee Silver Tier system
Coordinates watchers, orchestrator, scheduler, and audit logging
"""
import sys
import signal
import threading
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from polling_watcher import PollingBasedWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher
from orchestrator import Orchestrator
from scheduler import TaskScheduler
from skills.audit_logger import AuditLogger
import logging
import time


class SilverTierSystem:
    """Main system coordinator for Silver Tier AI Employee"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.running = False
        
        # Initialize components
        self._setup_logging()
        self._initialize_components()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Silver Tier System initialized")
    
    def _setup_logging(self):
        """Setup logging"""
        log_dir = self.project_path / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f'silver_tier_{time.strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _initialize_components(self):
        """Initialize all system components"""
        project_path_str = str(self.project_path)
        
        # Initialize audit logger
        self.audit_logger = AuditLogger(project_path_str)
        
        # Initialize watchers
        self.file_watcher = PollingBasedWatcher(project_path_str, check_interval=10)
        self.gmail_watcher = GmailWatcher(project_path_str, check_interval=120)
        self.whatsapp_watcher = WhatsAppWatcher(project_path_str, check_interval=60)
        
        # Initialize orchestrator
        self.orchestrator = Orchestrator(project_path_str)
        
        # Initialize scheduler
        self.scheduler = TaskScheduler(project_path_str)
        
        self.logger.info("All components initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start_watchers(self):
        """Start all watcher threads"""
        self.logger.info("Starting watchers...")
        
        # Start file watcher in thread
        self.file_watcher_thread = threading.Thread(
            target=self.file_watcher.run,
            daemon=True,
            name="FileWatcher"
        )
        self.file_watcher_thread.start()
        
        # Start Gmail watcher in thread
        self.gmail_watcher_thread = threading.Thread(
            target=self.gmail_watcher.run,
            daemon=True,
            name="GmailWatcher"
        )
        self.gmail_watcher_thread.start()
        
        # Start WhatsApp watcher in thread
        self.whatsapp_watcher_thread = threading.Thread(
            target=self.whatsapp_watcher.run,
            daemon=True,
            name="WhatsAppWatcher"
        )
        self.whatsapp_watcher_thread.start()
        
        self.logger.info("All watchers started")
    
    def start_scheduler(self):
        """Start the task scheduler"""
        self.logger.info("Starting scheduler...")
        self.scheduler.start()
        self.logger.info(f"Scheduled jobs: {self.scheduler.get_scheduled_jobs()}")
    
    def run_orchestrator_loop(self):
        """Run the orchestrator main loop"""
        self.logger.info("Starting orchestrator loop...")
        
        while self.running:
            try:
                # Check for new tasks
                new_tasks = self.orchestrator.check_needs_action()
                
                for task_file in new_tasks:
                    self.logger.info(f"Processing new task: {task_file.name}")
                    
                    # Create a plan
                    plan_file = self.orchestrator.create_plan(task_file)
                    
                    if plan_file:
                        # Process with Claude (simulated)
                        self.orchestrator.process_with_claude(plan_file)
                
                # Check for approved actions
                approved_actions = self.orchestrator.check_approved_actions()
                
                for approval_file in approved_actions:
                    self.logger.info(f"Executing approved action: {approval_file.name}")
                    self.orchestrator.execute_approved_action(approval_file)
                
                # Log system heartbeat
                self.audit_logger.log(
                    action_type="system_heartbeat",
                    actor="silver_tier_system",
                    result="success",
                    category=AuditLogger.CATEGORY_SYSTEM
                )
                
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in orchestrator loop: {e}")
                self.audit_logger.log(
                    action_type="orchestrator_error",
                    actor="silver_tier_system",
                    result="failed",
                    error=str(e),
                    category=AuditLogger.CATEGORY_SYSTEM
                )
                time.sleep(10)
    
    def start(self):
        """Start the complete Silver Tier system"""
        self.logger.info("=" * 50)
        self.logger.info("Starting AI Employee Silver Tier System")
        self.logger.info("=" * 50)
        
        self.running = True
        
        # Start all components
        self.start_watchers()
        self.start_scheduler()
        
        # Log startup
        self.audit_logger.log(
            action_type="system_startup",
            actor="silver_tier_system",
            result="success",
            category=AuditLogger.CATEGORY_SYSTEM
        )
        
        # Run main orchestrator loop (blocking)
        try:
            self.run_orchestrator_loop()
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        
        # Shutdown
        self.stop()
    
    def stop(self):
        """Stop the system gracefully"""
        self.logger.info("Stopping AI Employee Silver Tier System...")
        self.running = False
        
        # Stop scheduler
        if hasattr(self, 'scheduler'):
            self.scheduler.stop()
        
        # Log shutdown
        self.audit_logger.log(
            action_type="system_shutdown",
            actor="silver_tier_system",
            result="success",
            category=AuditLogger.CATEGORY_SYSTEM
        )
        
        self.logger.info("System stopped")


def main():
    """Main entry point"""
    print("=" * 50)
    print("AI Employee Silver Tier")
    print("=" * 50)
    print(f"Project path: {project_root}")
    print("\nStarting system...")
    print("Press Ctrl+C to stop\n")
    
    system = SilverTierSystem(str(project_root))
    system.start()


if __name__ == "__main__":
    main()
