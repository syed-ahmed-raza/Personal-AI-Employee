import os
import re
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import ssl

# --- RICH CONSOLE (Optional fallback if not installed) ---
try:
    from rich.console import Console
    console = Console()
    def cprint(msg, style=""):
        console.print(msg, style=style)
except ImportError:
    def cprint(msg, style=""):
        print(msg) # Fallback to standard print

# --- SENDGRID SETUP ---
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# --- MCP SETUP ---
try:
    from social_media_mcp import SocialMediaMCP
    SOCIAL_MEDIA_MCP_AVAILABLE = True
except ImportError:
    SOCIAL_MEDIA_MCP_AVAILABLE = False

# --- 🔥 CRITICAL SSL BYPASS FIX 🔥 ---
# This forces Python to ignore SSL Certificate errors (Fix for Pakistan ISPs/Networks)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
# -------------------------------------


class ActionEngine:
    """Executes approved plans with Robust Email Parsing and SSL Bypass."""

    def __init__(self, vault_path, check_interval=5):
        self.vault_path = Path(vault_path)
        self.approved_path = self.vault_path / 'Approved'
        self.done_path = self.vault_path / 'Done'
        self.rejected_path = self.vault_path / 'Rejected'
        self.dashboard_path = self.vault_path / 'Dashboard.md'
        self.check_interval = check_interval
        
        # Setup Logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('ActionEngine')

        # Load .env
        env_path = self.vault_path / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            self.logger.warning(".env file missing!")
        
        # Initialize SendGrid
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL")
        self.sg = None
        
        if SENDGRID_AVAILABLE and self.sendgrid_api_key and self.sendgrid_api_key.startswith("SG."):
            self.sg = SendGridAPIClient(self.sendgrid_api_key)
            self.logger.info("✅ SendGrid client initialized.")
        else:
            self.logger.warning("⚠️ SendGrid not configured correctly.")

        # Initialize MCPs
        self.social_media_mcp = None
        if SOCIAL_MEDIA_MCP_AVAILABLE:
            self.social_media_mcp = SocialMediaMCP(self.vault_path)
            self.logger.info("✅ SocialMediaMCP initialized.")

        # Create Folders
        self.approved_path.mkdir(exist_ok=True)
        self.done_path.mkdir(exist_ok=True)
        self.rejected_path.mkdir(exist_ok=True)

    def update_dashboard(self, task_name, status, executor="ActionEngine"):
        """Updates the Dashboard.md file."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Simple Append Mode for reliability
        log_entry = f"\n| {now} | {task_name} | {status} | {executor} |"
        
        try:
            with open(self.dashboard_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

    def process_files(self):
        """Scans Approved folder and executes actions."""
        # Use glob to find .md files
        files = list(self.approved_path.glob("PLAN_*.md"))
        
        for plan_path in files:
            filename = plan_path.name
            task_name = filename.replace("PLAN_", "").replace(".md", "")
            self.logger.info(f"⚡️ Executing approved plan: {task_name}")
            
            final_status = "Skipped"
            
            try:
                plan_content = plan_path.read_text(encoding="utf-8").strip()

                # --- 1. SOCIAL MEDIA ACTION ---
                if "post to twitter" in plan_content.lower() or "post to linkedin" in plan_content.lower():
                    platform = "Twitter" if "post to twitter" in plan_content.lower() else "LinkedIn"
                    cprint(f"Executing [bold blue]Social Media Post[/bold blue] to {platform}...", style="yellow")
                    
                    if self.social_media_mcp:
                        result = self.social_media_mcp.post_to_platform(platform, plan_content)
                        final_status = "✅ Posted (MCP)" if result == "Success" else "❌ Failed (MCP)"
                    else:
                        self.logger.info(f"[MOCK] Posted to {platform}: {plan_content[:50]}...")
                        final_status = "✅ Posted (Mock)"

                    self.update_dashboard(f"Social: {task_name}", final_status)
                    shutil.move(str(plan_path), str(self.done_path / filename))

                # --- 2. EMAIL ACTION ---
                elif "email" in plan_content.lower() or "send" in plan_content.lower():
                    if not self.sg:
                        final_status = "❌ Failed (No API Key)"
                        self.update_dashboard(f"Email: {task_name}", final_status)
                        shutil.move(str(plan_path), str(self.rejected_path / filename))
                        continue

                    # --- IMPROVED REGEX Extraction ---
                    # 1. Try to find explicit "To:" field (handles **To:**, To :, etc.)
                    to_email_match = re.search(r'(?:To|Recipient)[:\s\*-]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', plan_content, re.IGNORECASE)
                    
                    # 2. Fallback: Find ANY email in the file if specific tag missing
                    if not to_email_match:
                         to_email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', plan_content)

                    subject_match = re.search(r'(?:Subject)[:\s\*-]*(.+)', plan_content, re.IGNORECASE)
                    
                    # Extract Data
                    to_email = to_email_match.group(1).strip() if to_email_match else None
                    subject = subject_match.group(1).strip() if subject_match else "Update from AI Employee"
                    
                    # Body is everything else or the whole content
                    body = plan_content

                    if not to_email:
                        final_status = "⚠️ Failed (No Email Found)"
                        self.logger.warning(f"Could not find an email address in {filename}")
                        self.update_dashboard(f"Email: {task_name}", final_status)
                        shutil.move(str(plan_path), str(self.rejected_path / filename))
                        continue

                    cprint(f"Executing [bold green]SendGrid Email[/bold green] to {to_email}...", style="yellow")
                    
                    message = Mail(
                        from_email=self.from_email,
                        to_emails=to_email,
                        subject=subject,
                        html_content=f"<p>{body.replace(chr(10), '<br>')}</p>"
                    )
                    
                    try:
                        response = self.sg.send(message)
                        cprint(f"📧 Email sent! Status: {response.status_code}", style="green")
                        final_status = "✅ Email Sent"
                        self.update_dashboard(f"Email: {task_name}", final_status)
                        shutil.move(str(plan_path), str(self.done_path / filename))
                    except Exception as e:
                        cprint(f"❌ API Error: {e}", style="red")
                        final_status = "❌ API Error"
                        self.update_dashboard(f"Email: {task_name}", final_status)
                        shutil.move(str(plan_path), str(self.rejected_path / filename))

                # --- 3. GENERIC ARCHIVE (If no keyword matches) ---
                else:
                    self.logger.info(f"No specific action detected for {filename}. Moving to Done.")
                    shutil.move(str(plan_path), str(self.done_path / filename))

            except Exception as e:
                self.logger.error(f"Critical Error processing {filename}: {e}")
                shutil.move(str(plan_path), str(self.rejected_path / filename))

    def run(self):
        self.logger.info("⚡️ Action Engine Activated (SSL Bypass + Smart Regex). Watching /Approved...")
        while True:
            self.process_files()
            time.sleep(self.check_interval)

if __name__ == '__main__':
    # Auto-detect vault path
    current_path = Path(__file__).resolve()
    vault_path = current_path.parent.parent # Assuming src/action_engine.py -> AI_Employee_Vault
    
    engine = ActionEngine(vault_path)
    engine.run()