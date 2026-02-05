import time
import logging
import shutil
import os
from watchdog.events import FileSystemEventHandler
from pathlib import Path

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logger = logging.getLogger('FilesystemWatcher')
        
        # Ensure destination exists
        if not self.needs_action.exists():
            self.needs_action.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        if event.is_directory:
            return
        
        # Slight delay to ensure file handle is released by OS
        time.sleep(0.5)
        self.process_file(event.src_path)

    def process_file(self, src_path):
        filename = os.path.basename(src_path)
        dest_path = self.needs_action / filename
        
        # Retry loop for Windows PermissionError
        max_retries = 5
        for attempt in range(max_retries):
            try:
                shutil.move(src_path, dest_path)
                self.logger.info(f"✅ Moved {filename} to Needs_Action")
                self.create_metadata(filename)
                return
            except (PermissionError, OSError):
                self.logger.warning(f"⏳ File busy, retrying ({attempt+1}/{max_retries})...")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"❌ Error moving file: {e}")
                return
        
        self.logger.error(f"❌ Failed to move {filename} after {max_retries} attempts.")

    def create_metadata(self, filename):
        """Creates a companion markdown file for the AI to read"""
        meta_filename = f"{filename}.md"
        meta_path = self.needs_action / meta_filename
        
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                content = f"""---
type: file_drop
original_name: {filename}
received: {time.strftime('%Y-%m-%d %H:%M:%S')}
status: unread
---
New file received via Dropzone.
"""
                f.write(content)
        except Exception as e:
            self.logger.error(f"Failed to create metadata: {e}")