"""
Ralph Wiggum Plugin for AI Employee Silver Tier
Implements the persistence loop pattern to keep Claude Code working until tasks are complete

Based on: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
"""
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class RalphWiggumPlugin:
    """
    Ralph Wiggum persistence loop plugin
    
    This plugin intercepts Claude Code's exit and re-injects the prompt
    if the task is not yet complete, creating a persistence loop.
    """
    
    def __init__(self, project_path: str = None, max_iterations: int = 10):
        if project_path is None:
            self.project_path = project_root
        else:
            self.project_path = Path(project_path)
        
        self.max_iterations = max_iterations
        self.current_iteration = 0
        
        # Directories
        self.plans = self.project_path / 'plans'
        self.done = self.project_path / 'done'
        self.needs_action = self.project_path / 'needs_action'
        self.logs = self.project_path / 'logs'
        self.state = self.project_path / '.ralph_state'
        
        # Create directories
        for folder in [self.plans, self.done, self.needs_action, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Load state
        self._load_state()
        
        self.logger.info("Ralph Wiggum Plugin initialized")
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs / f'ralph_wiggum_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _load_state(self):
        """Load plugin state from file"""
        if self.state.exists():
            try:
                state = json.loads(self.state.read_text())
                self.current_iteration = state.get('iteration', 0)
                self.current_task = state.get('current_task')
                self.start_time = state.get('start_time')
            except:
                self.current_iteration = 0
                self.current_task = None
                self.start_time = None
        else:
            self.current_iteration = 0
            self.current_task = None
            self.start_time = None
    
    def _save_state(self):
        """Save plugin state to file"""
        state = {
            'iteration': self.current_iteration,
            'current_task': self.current_task,
            'start_time': self.start_time or datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
        self.state.write_text(json.dumps(state, indent=2))
    
    def start_task(self, task_description: str) -> Dict:
        """
        Start a new task with Ralph Wiggum loop
        
        Args:
            task_description (str): Description of the task to complete
            
        Returns:
            dict: Task state information
        """
        self.current_iteration = 0
        self.current_task = task_description
        self.start_time = datetime.now().isoformat()
        self._save_state()
        
        # Create task state file
        task_file = self.plans / f'RALPH_TASK_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        task_content = f"""---
type: ralph_task
created: {datetime.now().isoformat()}
status: in_progress
iteration: 0
max_iterations: {self.max_iterations}
---

# Ralph Wiggum Task

## Task Description
{task_description}

## Iteration Log
"""
        task_file.write_text(task_content, encoding='utf-8')
        
        self.logger.info(f"Ralph Wiggum task started: {task_file}")
        
        return {
            "status": "success",
            "message": "Ralph Wiggum loop started",
            "task_file": str(task_file),
            "max_iterations": self.max_iterations,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_completion(self, completion_criteria: str = None) -> bool:
        """
        Check if the current task is complete
        
        Args:
            completion_criteria (str): Optional criteria to check
            
        Returns:
            bool: True if task is complete
        """
        # Check if max iterations reached
        if self.current_iteration >= self.max_iterations:
            self.logger.warning(f"Max iterations ({self.max_iterations}) reached")
            return True
        
        # Check for completion markers
        # Strategy 1: Check if task file moved to done
        for file_pattern in ['RALPH_TASK_*.md', 'PLAN_*.md']:
            for file_path in self.done.glob(file_pattern):
                content = file_path.read_text().lower()
                if 'status: completed' in content or 'status: done' in content:
                    self.logger.info(f"Task marked complete: {file_path}")
                    return True
        
        # Strategy 2: Check for completion promise in output
        if completion_criteria:
            # Check logs for completion marker
            log_file = self.logs / f'claude_output_{datetime.now().strftime("%Y%m%d")}.txt'
            if log_file.exists():
                content = log_file.read_text()
                if completion_criteria.lower() in content.lower():
                    self.logger.info(f"Completion criteria found: {completion_criteria}")
                    return True
        
        # Strategy 3: Check if all items in needs_action have been processed
        needs_action_count = len(list(self.needs_action.glob('*.md')))
        if needs_action_count == 0:
            self.logger.info("All items processed")
            return True
        
        return False
    
    def should_continue(self) -> bool:
        """
        Determine if the Ralph Wiggum loop should continue
        
        Returns:
            bool: True if loop should continue
        """
        if self.current_iteration >= self.max_iterations:
            return False
        
        # Check if there's still work to do
        pending_items = (
            len(list(self.needs_action.glob('*.md'))) +
            len(list((self.project_path / 'pending_approval').glob('*.md')))
        )
        
        return pending_items > 0
    
    def increment_iteration(self, output: str = None) -> Dict:
        """
        Increment the iteration counter and log output
        
        Args:
            output (str): Claude's output from this iteration
            
        Returns:
            dict: Updated state information
        """
        self.current_iteration += 1
        self._save_state()
        
        # Log the iteration
        self.logger.info(f"Iteration {self.current_iteration}/{self.max_iterations}")
        
        # Update task file
        for file_path in self.plans.glob('RALPH_TASK_*.md'):
            content = file_path.read_text()
            content += f"""

## Iteration {self.current_iteration}
- **Time**: {datetime.now().isoformat()}
- **Output**: {output[:500] if output else 'No output captured'}
"""
            file_path.write_text(content, encoding='utf-8')
            break
        
        return {
            "status": "continuing",
            "iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "remaining": self.max_iterations - self.current_iteration,
            "timestamp": datetime.now().isoformat()
        }
    
    def create_continuation_prompt(self, original_prompt: str, previous_output: str) -> str:
        """
        Create a continuation prompt for the next iteration
        
        Args:
            original_prompt (str): The original task prompt
            previous_output (str): Claude's previous output
            
        Returns:
            str: Continuation prompt
        """
        return f"""{original_prompt}

---
PREVIOUS ATTEMPT OUTPUT:
{previous_output[:2000] if previous_output else 'No previous output'}

---
CONTINUATION INSTRUCTIONS:
The task is not yet complete. Review your previous output and continue working.
Check if there are any remaining items to process in /needs_action.
Update the plan files with your progress.
Move completed items to /done when finished.

Remember: Keep working until all tasks are complete or you reach max iterations.
"""
    
    def run_loop(self, prompt: str, claude_command: str = "claude") -> Dict:
        """
        Run the full Ralph Wiggum loop
        
        Args:
            prompt (str): The task prompt
            claude_command (str): Command to run Claude Code
            
        Returns:
            dict: Final result
        """
        self.logger.info(f"Starting Ralph Wiggum loop with prompt: {prompt[:100]}...")
        
        # Start the task
        self.start_task(prompt)
        
        current_prompt = prompt
        all_output = []
        
        while self.should_continue() and self.current_iteration < self.max_iterations:
            self.logger.info(f"Running iteration {self.current_iteration + 1}")
            
            # Run Claude Code with the prompt
            try:
                result = subprocess.run(
                    [claude_command, "--prompt", current_prompt],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per iteration
                )
                
                output = result.stdout
                all_output.append(output)
                
                # Save output to log
                log_file = self.logs / f'claude_iteration_{self.current_iteration + 1}.txt'
                log_file.write_text(output, encoding='utf-8')
                
                # Check completion
                if self.check_completion():
                    self.logger.info("Task completed successfully")
                    return {
                        "status": "completed",
                        "iterations": self.current_iteration + 1,
                        "output": output,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Prepare continuation
                current_prompt = self.create_continuation_prompt(prompt, output)
                self.increment_iteration(output)
                
            except subprocess.TimeoutExpired:
                self.logger.error(f"Iteration {self.current_iteration + 1} timed out")
                self.increment_iteration("TIMEOUT")
            except Exception as e:
                self.logger.error(f"Error in iteration: {e}")
                self.increment_iteration(f"ERROR: {e}")
        
        # Max iterations reached
        self.logger.warning("Max iterations reached without completion")
        return {
            "status": "max_iterations_reached",
            "iterations": self.current_iteration,
            "output": all_output[-1] if all_output else "No output",
            "timestamp": datetime.now().isoformat()
        }
    
    def stop(self):
        """Stop the Ralph Wiggum loop"""
        self._save_state()
        
        # Update any open task files
        for file_path in self.plans.glob('RALPH_TASK_*.md'):
            content = file_path.read_text()
            if 'status: in_progress' in content:
                content = content.replace('status: in_progress', 'status: stopped')
                content += f"\n## Stopped\n- **Time**: {datetime.now().isoformat()}\n"
                file_path.write_text(content, encoding='utf-8')
        
        self.logger.info("Ralph Wiggum loop stopped")
    
    def get_status(self) -> Dict:
        """Get current plugin status"""
        return {
            "status": "active" if self.should_continue() else "idle",
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "current_task": self.current_task,
            "start_time": self.start_time,
            "timestamp": datetime.now().isoformat()
        }


# CLI interface for testing
def main():
    """Test the Ralph Wiggum plugin"""
    print("=== Ralph Wiggum Plugin Test ===\n")
    
    plugin = RalphWiggumPlugin(str(project_root), max_iterations=5)
    
    # Get status
    print("Plugin status:")
    print(json.dumps(plugin.get_status(), indent=2))
    
    # Test starting a task
    print("\nStarting test task...")
    result = plugin.start_task("Process all files in /needs_action folder")
    print(json.dumps(result, indent=2))
    
    # Test iteration
    print("\nTesting iteration...")
    result = plugin.increment_iteration("Test output from Claude")
    print(json.dumps(result, indent=2))
    
    # Test completion check
    print("\nChecking completion...")
    is_complete = plugin.check_completion()
    print(f"Task complete: {is_complete}")


if __name__ == "__main__":
    main()
