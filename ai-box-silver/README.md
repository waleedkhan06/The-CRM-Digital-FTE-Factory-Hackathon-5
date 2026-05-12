# AI Employee Silver Tier - Autonomous Digital FTE

**Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

A comprehensive AI Employee system that proactively manages your personal and business communications using Claude Code as the reasoning engine and local file storage as the memory/dashboard.

## 🏆 Silver Tier Features

✅ **Implemented:**
- [x] **File System Watcher** - Monitors inbox for new files
- [x] **Gmail Watcher** - Monitors Gmail for new messages (OAuth2)
- [x] **WhatsApp Watcher** - Monitors WhatsApp Web for keyword messages
- [x] **Claude Reasoning Loop** - Creates Plan.md files for task tracking
- [x] **Email MCP Server** - Send and draft emails via Gmail API
- [x] **LinkedIn Poster** - Schedule and post business updates
- [x] **Human-in-the-Loop Approval** - All sensitive actions require approval
- [x] **Task Scheduler** - Daily briefings, weekly audits, scheduled posts
- [x] **Ralph Wiggum Persistence** - Keeps working until tasks are complete
- [x] **Comprehensive Audit Logging** - 90-day retention with integrity verification

## 📋 Requirements

### Software
- Python 3.12+ 
- Node.js 18+ (for Claude Code)
- Claude Code subscription
- Obsidian (optional, for dashboard viewing)

### Hardware
- Minimum: 8GB RAM, 4-core CPU, 20GB free disk
- Recommended: 16GB RAM, 8-core CPU, SSD storage

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd silver-tier-ai-employee

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials (optional for demo mode)
nano .env
```

### 3. Run Tests

```bash
# Run the test suite to verify installation
python test_silver_tier.py
```

### 4. Start the System

```bash
# Start the AI Employee system
python main.py
```

## 📁 Folder Structure

```
silver-tier-ai-employee/
├── inbox/              # Drop zone for new files to process
├── needs_action/       # Items requiring AI processing
├── plans/              # Active processing plans (Plan.md files)
├── pending_approval/   # ⭐ REVIEW HERE - Awaiting human approval
├── approved/           # Approved items ready for execution
├── rejected/           # Rejected items
├── done/               # Completed items archive
├── logs/               # System and audit logs
│   └── audit/          # Structured audit logs (JSONL)
├── drafts/             # Email drafts
├── sessions/           # Browser sessions (WhatsApp)
├── watchers/           # Perception scripts
│   ├── base_watcher.py
│   ├── filesystem_watcher.py
│   ├── gmail_watcher.py
│   └── whatsapp_watcher.py
├── mcp_servers/        # Action servers
│   └── email_mcp.py
├── skills/             # Agent skills/modules
│   ├── file_manager.py
│   ├── process_task.py
│   ├── update_dashboard.py
│   ├── linkedin_poster.py
│   ├── approval_workflow.py
│   └── audit_logger.py
├── main.py             # Main entry point
├── orchestrator.py     # Task coordination
├── scheduler.py        # Scheduled operations
├── ralph_wiggum.py     # Persistence loop
├── dashboard.md        # System status dashboard
├── company_handbook.md # Rules and guidelines
├── .env                # Environment configuration (DO NOT COMMIT)
└── README.md           # This file
```

## 🔧 Configuration

### Gmail API Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add to `.env`:
   ```
   GMAIL_CLIENT_ID=your_client_id
   GMAIL_CLIENT_SECRET=your_client_secret
   GMAIL_REFRESH_TOKEN=your_refresh_token
   GMAIL_DEMO_MODE=false
   ```

### LinkedIn API Setup (Optional)

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create an application
3. Get Client ID and Secret
4. Add to `.env`:
   ```
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_DEMO_MODE=false
   ```

### WhatsApp Setup (Optional)

1. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```
2. Enable in `.env`:
   ```
   WHATSAPP_ENABLED=true
   ```

## 📖 Usage

### Adding Tasks

1. **File Drop**: Place any file (.txt, .md, .pdf, .docx, .csv) in `/inbox`
2. **Direct Creation**: Create markdown files directly in `/needs_action`

### Approving Actions

1. Navigate to `/pending_approval` folder
2. Review the approval request file
3. **To Approve**: Move file to `/approved` folder
4. **To Reject**: Move file to `/rejected` folder

### Viewing Status

1. Open `dashboard.md` in Obsidian or any text editor
2. Check `/logs` for detailed system logs
3. Review `/logs/audit/` for structured audit logs

## 📅 Scheduled Operations

### Daily Tasks
| Time | Task | Description |
|------|------|-------------|
| 08:00 | Daily Briefing | Morning status report |
| 18:00 | EOD Summary | End of day summary |
| 00:00 | Cleanup | Expired approval cleanup |

### Weekly Tasks
| Day/Time | Task | Description |
|----------|------|-------------|
| Monday 07:00 | Weekly Audit | Business audit report |
| Wednesday 09:00 | LinkedIn Post | Scheduled business post |
| Friday 16:00 | Friday Report | Weekly status summary |

## 🔒 Security

### Credential Management
- Never commit `.env` file to version control
- Use environment variables for API keys
- Rotate credentials monthly
- Demo mode enabled by default for safety

### Human-in-the-Loop
All sensitive actions require approval:
- Email sending
- LinkedIn posting
- Any payment-related actions
- New contact communications

### Audit Logging
- All actions logged with timestamps
- 90-day retention policy
- Tamper-evident with hash verification
- Query and export capabilities

## 🧪 Testing

```bash
# Run full test suite
python test_silver_tier.py

# Expected output:
# ✓ ALL TESTS PASSED - SILVER TIER IMPLEMENTATION COMPLETE!
# Requirements: 8/8 met
```

## 🛠️ Troubleshooting

### Gmail Watcher Not Working
- Check credentials in `.env`
- Verify OAuth tokens are valid
- Check `/logs/gmail_watcher_*.log` for errors

### WhatsApp Watcher Not Working
- Install Playwright: `playwright install chromium`
- Enable in `.env`: `WHATSAPP_ENABLED=true`
- Check `/logs/whatsapp_watcher_*.log`

### System Not Processing Tasks
- Check orchestrator logs: `/logs/orchestrator_*.log`
- Verify files are in `/needs_action` folder
- Check for approval requests in `/pending_approval`

## 📚 Documentation

- [Dashboard](./dashboard.md) - System status
- [Company Handbook](./company_handbook.md) - Rules and guidelines
- [Audit Logs](./logs/audit/) - Structured action logs

## 🎯 Silver Tier vs Other Tiers

| Feature | Bronze | Silver ✅ | Gold |
|---------|--------|-----------|------|
| File Watcher | ✓ | ✓ | ✓ |
| Gmail Watcher | - | ✓ | ✓ |
| WhatsApp Watcher | - | ✓ | ✓ |
| Email MCP | - | ✓ | ✓ |
| LinkedIn Poster | - | ✓ | ✓ |
| Approval Workflow | - | ✓ | ✓ |
| Scheduler | - | ✓ | ✓ |
| Ralph Wiggum Loop | - | ✓ | ✓ |
| Audit Logging | - | ✓ | ✓ |
| Odoo Integration | - | - | ✓ |
| Facebook/Instagram | - | - | ✓ |
| Twitter (X) | - | - | ✓ |
| CEO Briefing | - | - | ✓ |

## 🤝 Contributing

This is part of the Personal AI Employee Hackathon 0. For more information:
- Join Wednesday meetings on Zoom
- Check the main [ai-employee.md](../ai-employee.md) documentation
- Submit your implementation via the hackathon form

## 📄 License

This project is part of an educational hackathon. Use responsibly and ethically.

## ⚠️ Disclaimer

- This system handles sensitive communications and data
- Always review and approve actions before execution
- Regularly audit system behavior
- Comply with all applicable laws and terms of service
- WhatsApp automation may violate WhatsApp's ToS - use at your own risk

---

*Generated by AI Employee Silver Tier v0.2*  
*Last Updated: 2026-03-02*
