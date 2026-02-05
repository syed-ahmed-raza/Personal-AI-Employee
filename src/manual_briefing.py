import os
import sys
from pathlib import Path
import logging

# Add the src directory to the Python path to allow sibling imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_engine import AgentEngine

# Configure basic logging for visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ManualBriefingTrigger')

def main():
    logger.info("Manual Briefing Trigger Started.")
    
    # Define Vault Path (Go up one level from src)
    vault_root = Path(__file__).resolve().parent.parent

    try:
        # Initialize the AgentEngine
        # AgentEngine's __init__ expects needs_action_dir, plans_dir, in_progress_dir.
        # We can pass the vault_root and let AgentEngine construct these paths internally.
        # However, the AgentEngine __init__ currently expects needs_action_dir, plans_dir, in_progress_dir as separate arguments.
        # Let's adjust the AgentEngine to take a single vault_path and derive its directories, or pass all required paths here.
        # For now, let's pass the derived paths as it was designed.

        engine = AgentEngine(vault_path=vault_root)
        
        # Directly call the generate_briefing method
        engine.generate_briefing()
        
        logger.info("✅ Briefing Generated! Check AI_Employee_Vault/Briefing_[Date].md")

    except Exception as e:
        logger.error(f"Error generating briefing: {e}", exc_info=True)
        logger.error("Failed to generate briefing. Ensure your GEMINI_API_KEY is set in AI_Employee_Vault/.env")

if __name__ == "__main__":
    main()
