import time
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BaseWatcher(ABC):
    """An abstract base class for all watchers."""
    def __init__(self, check_interval=5):
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def check_for_new_events(self):
        """The core logic of the watcher to check for new events."""
        pass

    def run(self):
        """Runs the watcher indefinitely."""
        self.logger.info("Watcher started.")
        while True:
            try:
                self.check_for_new_events()
            except Exception as e:
                self.logger.error(f"An error occurred: {e}", exc_info=True)
            time.sleep(self.check_interval)
