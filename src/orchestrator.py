import time
import logging
import concurrent.futures
import sys
import os

# --- PATH FIX: Ensure we can import sibling scripts ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# ----------------------------------------------------

from filesystem_watcher import DropFolderHandler
from agent_engine import AgentEngine
from action_engine import ActionEngine as ActionEngineExecutor
from system_watcher import SystemWatcher
from watchdog.observers import Observer

def run_filesystem_watcher(vault_path):
    event_handler = DropFolderHandler(vault_path)
    observer = Observer()
    input_path = os.path.join(vault_path, 'Input_Dropzone')
    
    if not os.path.exists(input_path):
        os.makedirs(input_path)
        
    observer.schedule(event_handler, input_path, recursive=False)
    observer.start()
    logging.info(f"👀 Filesystem Watcher Active on: {input_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def run_agent_engine(vault_path):
    engine = AgentEngine(vault_path)
    engine.run()

def run_action_engine(vault_path):
    action_engine = ActionEngineExecutor(vault_path)
    action_engine.run()

def run_system_watcher(vault_path):
    system_watcher = SystemWatcher(vault_path)
    system_watcher.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    logging.info("🚀 Starting Personal AI Employee System...")
    logging.info(f"📂 Vault Root: {BASE_DIR}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Start the components
        executor.submit(run_filesystem_watcher, BASE_DIR)
        executor.submit(run_agent_engine, BASE_DIR)
        executor.submit(run_action_engine, BASE_DIR)
        executor.submit(run_system_watcher, BASE_DIR)
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("🛑 Shutting down system...")