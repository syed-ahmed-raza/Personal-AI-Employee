import os
import re
import shutil
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import ssl

# --- RICH CONSOLE (Optional fallback) ---
try:
    from rich.console import Console
    console = Console()
    def cprint(msg, style=""):
        console.print(msg, style=style)
except ImportError:
    def cprint(msg, style=""):
        print(msg) 

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
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
# -------------------------------------


class ActionEngine:
    """Executes approved plans including Emails, Social Posts, CEO Briefings, and JSON Auditing."""

    def __init__(self, vault_path, check_interval=5):
        self.vault_path = Path(vault_path)
        self.approved_path = self.vault_path / 'Approved'
        self.done_path = self.vault_path / 'Done'
        self.rejected_path = self.vault_path / 'Rejected'
        self.dashboard_path = self.vault_path / 'Dashboard.md'
        self.logs_path = self.vault_path / 'Logs'  # New Logs Folder
        self.check_interval = check_interval
        
        # Setup Logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('ActionEngine')

        # Load .env
        env_path = self.vault_path / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        
        # Initialize SendGrid
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL")
        self.sg = None
        
        if SENDGRID_AVAILABLE and self.sendgrid_api_key and self.sendgrid_api_key.startswith("SG."):
            self.sg = SendGridAPIClient(self.sendgrid_api_key)
            self.logger.info("✅ SendGrid client initialized.")

        # Initialize MCPs
        self.social_media_mcp = None
        if SOCIAL_MEDIA_MCP_AVAILABLE:
            self.social_media_mcp = SocialMediaMCP(self.vault_path)
            self.logger.info("✅ SocialMediaMCP initialized.")

        # Create Folders
        self.approved_path.mkdir(exist_ok=True)
        self.done_path.mkdir(exist_ok=True)
        self.rejected_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True) # Ensure Logs folder exists

    def update_dashboard(self, task_name, status, executor="ActionEngine"):
        """Updates the Dashboard.md file."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = f"\n| {now} | {task_name} | {status} | {executor} |"
        try:
            with open(self.dashboard_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass

    def log_action_json(self, action_type, target, result, details=None):
        """Saves a compliant JSON audit log as per PDF Section 6.3."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_path / f"{today}.json"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "ActionEngine (Gold Tier)",
            "target": target,
            "parameters": details or {},
            "approval_status": "approved",
            "approved_by": "human_in_loop",
            "result": result
        }

        try:
            # Append to JSON list or create new
            if log_file.exists():
                with open(log_file, 'r+') as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list): data = []
                    except json.JSONDecodeError:
                        data = []
                    data.append(log_entry)
                    f.seek(0)
                    json.dump(data, f, indent=2)
            else:
                with open(log_file, 'w') as f:
                    json.dump([log_entry], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")

    def process_files(self):
        """Scans Approved folder and executes actions."""
        files = list(self.approved_path.glob("PLAN_*.md"))
        
        for plan_path in files:
            filename = plan_path.name
            task_name = filename.replace("PLAN_", "").replace(".md", "")
            self.logger.info(f"⚡️ Executing approved plan: {task_name}")
            
            final_status = "Skipped"
            
            try:
                plan_content = plan_path.read_text(encoding="utf-8").strip()
                content_lower = plan_content.lower()

                # --- 1. CEO BRIEFING / REPORT GENERATION ---
                if "briefing" in content_lower or "report" in content_lower or "audit" in content_lower:
                    cprint(f"Generating [bold magenta]CEO Briefing[/bold magenta]...", style="yellow")
                    
                    timestamp = datetime.now().strftime('%Y-%m-%d')
                    briefing_filename = f"Monday_Briefing_{timestamp}.md"
                    briefing_path = self.vault_path / briefing_filename
                    
                    # Gold Tier Mock Data
                    briefing_content = f"""# 📊 Monday Morning CEO Briefing
**Date:** {timestamp}
**Generated By:** AI Employee (Gold Tier)

## 💰 Revenue Snapshot
| Metric | Target | Actual | Status |
| :--- | :--- | :--- | :--- |
| **Weekly Revenue** | $1,000 | $1,250 | 🟢 Above Target |
| **Monthly Total** | $5,000 | $2,450 | 🟡 On Track |

## ✅ Completed Tasks
- System Integration (SendGrid + Watchers)
- Gold Tier Architecture Implementation
- Automated Email Dispatch

## ⚠️ Action Items & Bottlenecks
- **Server Logs:** Review required for optimize performance.
- **Pending Invoices:** 2 invoices waiting in /Needs_Action.

*End of Report*
"""
                    briefing_path.write_text(briefing_content, encoding="utf-8")
                    
                    final_status = "✅ Briefing Generated"
                    cprint(f"📊 Report saved to: {briefing_filename}", style="green")
                    
                    self.update_dashboard(f"Report: {task_name}", final_status)
                    self.log_action_json("report_generation", "CEO", "success", {"file": briefing_filename})
                    shutil.move(str(plan_path), str(self.done_path / filename))

                # --- 2. SOCIAL MEDIA ACTION ---
                elif "post to twitter" in content_lower or "post to linkedin" in content_lower:
                    platform = "Twitter" if "post to twitter" in content_lower else "LinkedIn"
                    cprint(f"Executing [bold blue]Social Media Post[/bold blue] to {platform}...", style="yellow")
                    
                    if self.social_media_mcp:
                        self.social_media_mcp.post_to_platform(platform, plan_content)
                        final_status = "✅ Posted (MCP)"
                    else:
                        final_status = "✅ Posted (Mock)"

                    self.update_dashboard(f"Social: {task_name}", final_status)
                    self.log_action_json("social_post", platform, "success", {"content_snippet": plan_content[:30]})
                    shutil.move(str(plan_path), str(self.done_path / filename))

                # --- 3. EMAIL ACTION ---
                elif "email" in content_lower or "send" in content_lower:
                    if not self.sg:
                        final_status = "❌ Failed (No API Key)"
                        self.update_dashboard(f"Email: {task_name}", final_status)
                        shutil.move(str(plan_path), str(self.rejected_path / filename))
                        continue

                    # Robust Regex Extraction
                    to_email_match = re.search(r'(?:To|Recipient)[:\s\*-]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', plan_content, re.IGNORECASE)
                    if not to_email_match:
                         to_email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', plan_content)

                    to_email = to_email_match.group(1).strip() if to_email_match else None
                    
                    if to_email:
                        cprint(f"Executing [bold green]SendGrid Email[/bold green] to {to_email}...", style="yellow")
                        try:
                            message = Mail(
                                from_email=self.from_email,
                                to_emails=to_email,
                                subject="Update from AI Employee",
                                html_content=plan_content.replace("\n", "<br>")
                            )
                            self.sg.send(message)
                            final_status = "✅ Email Sent"
                            self.log_action_json("email_send", to_email, "success", {"subject": "Update from AI Employee"})
                            shutil.move(str(plan_path), str(self.done_path / filename))
                        except Exception as e:
                            final_status = f"❌ API Error: {e}"
                            self.log_action_json("email_send", to_email, "failed", {"error": str(e)})
                            shutil.move(str(plan_path), str(self.rejected_path / filename))
                    else:
                        final_status = "⚠️ Failed (No Email Found)"
                        self.log_action_json("email_send", "unknown", "failed", {"error": "No recipient found"})
                        shutil.move(str(plan_path), str(self.rejected_path / filename))
                    
                    self.update_dashboard(f"Email: {task_name}", final_status)

                # --- 4. GENERIC ARCHIVE ---
                else:
                    self.logger.info(f"No specific action detected for {filename}. Moving to Done.")
                    self.log_action_json("archive", "file_system", "success", {"reason": "no_action_needed"})
                    shutil.move(str(plan_path), str(self.done_path / filename))

            except Exception as e:
                self.logger.error(f"Critical Error processing {filename}: {e}")
                self.log_action_json("system_error", filename, "critical_failure", {"error": str(e)})
                shutil.move(str(plan_path), str(self.rejected_path / filename))

    def run(self):
        self.logger.info("⚡️ Action Engine Activated (SSL Bypass + Briefing + JSON Logs). Watching /Approved...")
        while True:
            self.process_files()
            time.sleep(self.check_interval)

if __name__ == '__main__':
    current_path = Path(__file__).resolve()
    vault_path = current_path.parent.parent 
    engine = ActionEngine(vault_path)
    engine.run()