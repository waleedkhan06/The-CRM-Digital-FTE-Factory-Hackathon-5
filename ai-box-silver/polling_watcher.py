"""
Polling-based file watcher for AI Employee Bronze Tier
This alternative implementation polls the inbox folder instead of using filesystem events,
which should work better in environments where filesystem events don't work properly
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import sys

class PollingBasedWatcher:
    """Watches the inbox folder by periodically checking for new files"""

    def __init__(self, project_path: str, check_interval: int = 10):
        self.project_path = Path(project_path)
        self.inbox_path = self.project_path / 'inbox'
        self.needs_action = self.project_path / 'needs_action'
        self.check_interval = check_interval
        self.processed_files = set()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.project_path / 'logs' / f'polling_watcher_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create required directories if they don't exist
        self.inbox_path.mkdir(exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)

    def get_supported_files(self):
        """Get all supported files in inbox that haven't been processed yet"""
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.csv'}
        files = []

        for file_path in self.inbox_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if str(file_path) not in self.processed_files:
                    files.append(file_path)

        return files

    def create_action_file(self, file_path: Path):
        """Create an action file in the needs_action folder"""
        try:
            # Create metadata for the file
            file_stat = file_path.stat()
            metadata = {
                'original_path': str(file_path),
                'original_name': file_path.name,
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'extension': file_path.suffix,
                'type': 'file_drop'
            }

            # Create action file in needs_action folder
            action_filename = f"FILE_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            action_file_path = self.needs_action / action_filename

            action_content = f"""---
type: file_drop
original_name: {metadata['original_name']}
size: {metadata['size']} bytes
date_added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: pending
priority: medium
---

# New File Detected

## File Information
- **Name**: {metadata['original_name']}
- **Size**: {metadata['size']} bytes
- **Type**: {metadata['extension']}
- **Added**: {metadata['created']}

## Original Path
```
{metadata['original_path']}
```

## Recommended Actions
- [ ] Review file content
- [ ] Determine appropriate action
- [ ] Process or delegate as needed

## File Preview (First 500 chars)
```
{self.get_file_preview(file_path)}
```
"""

            action_file_path.write_text(action_content)
            self.logger.info(f"Action file created: {action_file_path}")
            return action_file_path

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None

    def get_file_preview(self, file_path: Path) -> str:
        """Get a preview of the file content (for text files)"""
        try:
            if file_path.suffix.lower() in ['.txt', '.md', '.csv']:
                content = file_path.read_text(encoding='utf-8')
                return content[:500]  # Return first 500 characters
            else:
                return f"[Binary file of type {file_path.suffix}]"
        except Exception as e:
            return f"[Could not read file preview: {e}]"

    def run(self):
        """Start watching the inbox folder by polling"""
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Watching folder: {self.inbox_path}')
        self.logger.info(f'Check interval: {self.check_interval} seconds')

        try:
            while True:
                files_to_process = self.get_supported_files()

                for file_path in files_to_process:
                    self.logger.info(f"New file detected: {file_path}")
                    self.create_action_file(file_path)
                    self.processed_files.add(str(file_path))

                if files_to_process:
                    self.logger.info(f"Processed {len(files_to_process)} new files")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Polling watcher stopped by user")
        except Exception as e:
            self.logger.error(f"Error in polling watcher: {e}")
            raise