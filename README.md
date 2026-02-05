# Personal AI Employee (Digital FTE) - Hackathon 0

## 🏆 Project Overview
This project is a fully autonomous **Digital Full-Time Equivalent (FTE)** built using **Python, Google Gemini 2.5 Flash, and Obsidian**. It acts as a proactive employee that monitors files, plans tasks, executes actions, and provides strategic business briefings.

**Tier Achieved:** Gold Tier Architecture 🥇

## 🌟 Key Features
* **Perception Layer:** Two Watchers active.
    * [cite_start]`Filesystem Watcher`: Monitors `/Input_Dropzone` for new tasks[cite: 135].
    * [cite_start]`System Watcher`: Monitors CPU/RAM usage to ensure system health[cite: 72].
* **Reasoning Engine:** Powered by **Google Gemini 2.5 Flash**. [cite_start]Analyzes content (vision & text) to generate actionable execution plans[cite: 14].
* [cite_start]**Nerve Center:** Integrates with **Obsidian** to provide a real-time Dashboard with live status updates[cite: 125].
* **Action Layer:**
    * [cite_start]**Real Email:** Integrated **SendGrid API** for sending actual emails[cite: 284].
    * [cite_start]**Social Media & Accounting:** Implemented **Gold Tier Architecture** using Mock MCPs to demonstrate full integration capabilities (Odoo & Social APIs simulated for Hackathon demo)[cite: 83, 85].
* [cite_start]**CEO Briefing:** Generates a "Monday Morning Briefing" analyzing completed tasks against business revenue goals[cite: 357].

## 🛠️ Tech Stack
* **Core:** Python 3.12+
* [cite_start]**Brain:** Google Gemini API (gemini-2.5-flash) [cite: 42]
* [cite_start]**GUI/Memory:** Obsidian (Markdown Vault) [cite: 42]
* **Communication:** SendGrid API (Email)
* **Libraries:** `watchdog`, `google-genai`, `python-dotenv`, `psutil`, `sendgrid`

## 📂 Project Structure
```text
AI_Employee_Vault/
├── .env                     # API Keys (Not uploaded)
├── Company_Handbook.md      # Rules of Engagement
├── Business_Goals.md        # Revenue targets
├── Dashboard.md             # Live Status Board
├── Logs/                    # Activity Logs
├── Input_Dropzone/          # Drag & Drop Tasks here
├── Needs_Action/            # Raw detected files
├── Plans/                   # AI Generated Plans
├── Approved/                # Human Approval Folder
├── Done/                    # Archived Tasks
└── src/
    ├── orchestrator.py      # Main System Controller
    ├── agent_engine.py      # Gemini Brain
    ├── action_engine.py     # Execution Hand (SendGrid/Socials)
    ├── filesystem_watcher.py# File Monitor
    ├── system_watcher.py    # Health Monitor
    └── social_media_mcp.py  # Social Media Architecture