import psutil
import time
import logging
from pathlib import Path
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SystemWatcher:
    def __init__(self, needs_action_dir="AI_Employee_Vault/Needs_Action"):
        self.needs_action_dir = Path(needs_action_dir)
        self.needs_action_dir.mkdir(exist_ok=True)

    def run(self):
        logging.info("Starting System Watcher...")
        while True:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            logging.info(f"System Watcher Active... CPU: {cpu_usage}%, RAM: {ram_usage}%")

            if cpu_usage > 90.0 or ram_usage > 90.0:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                alert_file_path = self.needs_action_dir / f"ALERT_High_Load_{timestamp}.txt"
                alert_content = f"Warning: High System Resource Usage detected!\nCPU: {cpu_usage}%\nRAM: {ram_usage}%"
                try:
                    with open(alert_file_path, 'w') as f:
                        f.write(alert_content)
                    logging.warning(f"High resource usage detected. Alert file created at {alert_file_path}")
                except Exception as e:
                    logging.error(f"Failed to write alert file: {e}")
            
            time.sleep(60)

if __name__ == '__main__':
    watcher = SystemWatcher()
    watcher.run()