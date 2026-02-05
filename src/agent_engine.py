import os
import time
import shutil
import logging
import warnings
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Suppress Warnings
warnings.filterwarnings("ignore")

# Try importing AI library
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

class AgentEngine:
    def __init__(self, vault_path, check_interval=5):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans_path = self.vault_path / 'Plans'
        self.in_progress = self.vault_path / 'In_Progress'
        self.done_path = self.vault_path / 'Done'
        self.dashboard_path = self.vault_path / 'Dashboard.md'
        self.goals_path = self.vault_path / 'Business_Goals.md'
        self.check_interval = check_interval
        
        # Setup Logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('AgentEngine')

        # Load Env
        env_path = self.vault_path / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Configure AI
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.model_name = "AI Unavailable" # Default to AI Unavailable

        if not self.api_key or self.api_key == "PASTE_YOUR_KEY_HERE":
            self.logger.warning("GEMINI_API_KEY not found or not set. AI capabilities disabled.")
        elif AI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                
                # --- Robust Model Selection ---
                selected_model_name = None
                try:
                    self.logger.info("🔍 Searching for available Gemini models...")
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            # Prefer models that don't require specific versioning if possible, or a flexible one
                            # This prioritizes 'gemini-1.5-flash' but is flexible
                            if 'gemini-1.5-flash' in m.name:
                                selected_model_name = m.name # Use the exact name if found
                                break
                            elif 'gemini-pro' in m.name: # Fallback to gemini-pro if flash not found
                                selected_model_name = m.name
                                break
                            elif 'gemini' in m.name: # Generic gemini
                                selected_model_name = m.name
                                break
                except Exception as e:
                    self.logger.warning(f"Could not list models from Gemini API: {e}")

                if selected_model_name:
                    self.model = genai.GenerativeModel(selected_model_name)
                    self.model_name = selected_model_name.replace('models/', '') # Clean up name for dashboard
                    self.logger.info(f"✨ AI Connected successfully using: {self.model_name}")
                else:
                    self.logger.error("❌ No suitable Gemini model found that supports 'generateContent'. AI capabilities disabled.")
                    self.model = None
                    self.model_name = "AI Unavailable (No Model)"

            except Exception as e:
                self.logger.error(f"❌ Failed to configure Gemini API: {e}")
                self.model = None
                self.model_name = "AI Unavailable (Config Error)"
        
        # Ensure folders exist
        self.in_progress.mkdir(exist_ok=True)
        self.plans_path.mkdir(exist_ok=True)
        self.done_path.mkdir(exist_ok=True)

    def ask_gemini(self, prompt, image_path=None):
        if not self.model:
            return None
        try:
            if image_path:
                try:
                    import PIL.Image
                    img = PIL.Image.open(image_path)
                    response = self.model.generate_content([prompt, img])
                except ImportError:
                    self.logger.warning("Pillow library not found, analyzing text only.")
                    return None
            else:
                response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            self.logger.error(f"AI Generation Error: {e}")
            return None

    def generate_plan_content(self, filename):
        file_path = self.in_progress / filename
        ai_response = None
        
        if self.model and file_path.exists():
            try:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    prompt = f"Act as a Personal AI Employee. Analyze this image file '{filename}'. Create a structured Plan.md with: # Objective, # Proposed Actions (Step-by-step), # Approval. Be professional."
                    ai_response = self.ask_gemini(prompt, image_path=file_path)
                elif filename.lower().endswith(('.txt', '.md', '.csv', '.py', '.js')):
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    prompt = f"Act as a Personal AI Employee. Read this file '{filename}':\n\n{content[:5000]}\n\nCreate a Plan.md with: # Objective, # Proposed Actions, # Approval."
                    ai_response = self.ask_gemini(prompt)
            except Exception as e:
                self.logger.warning(f"AI processing failed: {e}")

        if not ai_response:
            ai_response = f"""# Objective
Process file: **{filename}** (Manual Mode)
# Proposed Actions
- [ ] Review file manually (AI unavailable or file type unsupported)"""
        
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"---\nstatus: Pending Approval\ndate: {date_str}\ntarget_file: {filename}\n---\n\n{ai_response}"

    def update_dashboard(self, task_name, status, model_name):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_row = f"| {now} | {task_name} | {status} | {model_name} |"
        
        header_title = "## 🟢 Recent Activity"
        table_header = "| Timestamp | Task | Status | Model |"
        table_divider = "|---|---|---|---|"
        
        if not self.dashboard_path.exists():
            content = f"# Modern Futuristic HUD\n\n{header_title}\n{table_header}\n{table_divider}\n{new_row}\n"
            self.dashboard_path.write_text(content, encoding="utf-8")
            return
        try:
            lines = self.dashboard_path.read_text(encoding="utf-8").splitlines()
            header_index = lines.index(header_title) if header_title in lines else -1
            if header_index == -1:
                lines.extend(["\n", header_title, table_header, table_divider, new_row])
                self.dashboard_path.write_text("\n".join(lines), encoding="utf-8")
                return
            table_header_index = lines.index(table_header, header_index) if table_header in lines[header_index:] else -1
            if table_header_index == -1:
                lines.insert(header_index + 1, new_row); lines.insert(header_index + 1, table_divider); lines.insert(header_index + 1, table_header)
                self.dashboard_path.write_text("\n".join(lines), encoding="utf-8")
                return
            divider_index = lines.index(table_divider, table_header_index)
            table_rows = []; i = divider_index + 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_rows.append(lines[i]); i += 1
            updated_rows = [new_row] + table_rows[:4]
            final_lines = lines[:divider_index + 1] + updated_rows + lines[divider_index + 1 + len(table_rows):]
            self.dashboard_path.write_text("\n".join(final_lines), encoding="utf-8")
            self.logger.info(f"Dashboard updated for task: {task_name}")
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}", exc_info=True)

    def generate_briefing(self):
        """Generates a Monday Morning CEO Briefing."""
        self.logger.info("Generating CEO Briefing...")
        
        completed_tasks = [f for f in os.listdir(self.done_path) if os.path.isfile(self.done_path / f)]
        completed_tasks_list = "\n".join(f"- {task}" for task in completed_tasks[-20:])

        if not self.goals_path.exists():
            self.goals_path.write_text("# Weekly Business Goals\n\n## Revenue Targets\n| Week | Target | Actual |\n|---|---|---|\n| 2026-W6 | $3,000 | $0 |", encoding="utf-8")
        
        business_goals = self.goals_path.read_text(encoding="utf-8")

        prompt = f"You are a proactive Business AI Assistant. Review the data and write a 'Monday Morning CEO Briefing' in Markdown.\n\n**Data:**\n1. **Recently Completed Tasks:**\n{completed_tasks_list}\n\n2. **Current Business Goals:**\n{business_goals}\n\n**Instructions:**\n- Write a concise **Executive Summary**.\n- Analyze **Revenue vs Target**. Invent plausible revenue numbers based on tasks.\n- Identify potential **Bottlenecks**.\n- Provide **Proactive Suggestions**."
        
        briefing_content = self.ask_gemini(prompt) or "# Briefing Failed\nAI model unavailable."
        
        briefing_filename = f"Briefing_{datetime.now().strftime('%Y-%m-%d')}.md"
        briefing_path = self.vault_path / briefing_filename
        briefing_path.write_text(briefing_content, encoding="utf-8")
        self.logger.info(f"Successfully generated briefing: {briefing_filename}")
        self.update_dashboard(task_name="Generated CEO Briefing", status="📄 Report Ready", model_name=self.model_name)

    def process_files(self):
        try:
            files = [f for f in os.listdir(self.needs_action) if os.path.isfile(self.needs_action / f)]
            
            for file in files:
                if file == "GENERATE_BRIEFING":
                    try:
                        self.generate_briefing()
                        os.remove(self.needs_action / file)
                        self.logger.info("Briefing generated and trigger file removed.")
                    except Exception as e:
                        self.logger.error(f"Failed to generate briefing: {e}", exc_info=True)
                    continue

                if file.endswith(".md"): 
                    continue 

                self.logger.info(f"🧠 Thinking about: {file}...")
                
                try:
                    shutil.move(self.needs_action / file, self.in_progress / file)
                except Exception as e:
                    self.logger.error(f"Move failed: {e}")
                    continue

                plan_content = self.generate_plan_content(file)
                plan_path = self.plans_path / f"PLAN_{file}.md"
                plan_path.write_text(plan_content, encoding="utf-8")
                
                self.logger.info(f"💡 Plan created: {plan_path.name}")
                self.update_dashboard(f"Processed {file}", status="✅ Plan Ready", model_name=self.model_name)

        except Exception as e:
            self.logger.error(f"Error in process loop: {e}", exc_info=True)

    def run(self):
        self.logger.info("🧠 Agent Brain Activated.")
        while True:
            self.process_files()
            time.sleep(self.check_interval)

if __name__ == "__main__":
    engine = AgentEngine(r"../")
    engine.run()