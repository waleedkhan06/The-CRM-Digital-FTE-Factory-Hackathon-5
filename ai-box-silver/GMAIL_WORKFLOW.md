# 📧 Gmail Automation - Complete Workflow Guide

## 🎯 Overview

The Gmail automation system monitors your inbox, processes incoming emails, and sends replies - **ALL with Human-in-the-Loop (HITL) approval**.

---

## 📋 Complete Workflow (Step-by-Step)

### **STEP 1: Gmail Watcher Monitors Inbox**

**File:** `watchers/gmail_watcher.py`

**What it does:**
- Checks your Gmail every 2 minutes
- Looks for unread/important emails
- Creates action files for new emails

**Command:**
```bash
python watchers/gmail_watcher.py
```

**Result:**
- New email detected → Creates file in `needs_action/`

---

### **STEP 2: Email Saved to needs_action/**

**Folder:** `needs_action/`

**File created:** `EMAIL_{message_id}_{timestamp}.md`

**Example file:**
```markdown
---
type: email
from: client@example.com
to: khanwk800@gmail.com
subject: Project Inquiry
received: 2026-03-16T10:30:00
priority: high
status: pending
---

# Email Received

## Header Information
- **From**: client@example.com
- **To**: khanwk800@gmail.com
- **Subject**: Project Inquiry
- **Date**: 2026-03-16 10:30:00

## Email Content
Hi, I'm interested in your AI automation services.
Can you send me pricing information?

## Suggested Actions
- [ ] Read and understand the email
- [ ] Draft a response
- [ ] Take any required actions
- [ ] Mark as processed
```

**What you do:**
- Nothing yet! Watcher handles this automatically.

---

### **STEP 3: Orchestrator Creates Plan**

**File:** `orchestrator.py`

**What it does:**
- Reads email from `needs_action/`
- Analyzes content
- Creates plan file
- Determines if approval is needed

**Result:**
- Creates: `plans/PLAN_EMAIL_{timestamp}.md`

**Example plan:**
```markdown
---
type: plan
created: 2026-03-16T10:32:00
status: pending
priority: high
task_type: email
source_file: EMAIL_19cf3a334af87d68.md
---

# Plan: Email Processing

## Objective
Process email from client@example.com and respond appropriately.

## Steps
- [ ] Read and analyze the email content
- [ ] Determine required actions
- [ ] Check if approval is needed (YES - email reply)
- [ ] Create approval request
- [ ] Execute actions after approval
- [ ] Update dashboard
- [ ] Move to done when complete
```

---

### **STEP 4: Approval Request Created**

**Folder:** `pending_approval/`

**File created:** `APPROVAL_email_reply_{timestamp}.md`

**Example file:**
```markdown
---
type: approval_request
action: email_reply
created: 2026-03-16T10:33:00
status: pending
requires_human_approval: true
source_email: client@example.com
subject: Re: Project Inquiry
---

# Email Reply Approval Required ⚠️ HUMAN-IN-THE-LOOP

## Email Details
- **To**: client@example.com
- **Subject**: Re: Project Inquiry
- **Priority**: high

## Proposed Reply:
```
Dear Client,

Thank you for your interest in our AI automation services!

I'd be happy to send you our pricing information.
We offer several packages starting at $500/month.

Would you like to schedule a call to discuss your specific needs?

Best regards,
AI Employee System
```

## Human-in-the-Loop Requirement
This email reply CANNOT be sent without your explicit approval.

## To APPROVE:
1. Review the reply content above
2. Edit if needed
3. Move this file to `/approved/` folder
4. The system will send the email automatically

## To REJECT:
1. Move this file to `/rejected/` folder, OR
2. Delete this file
3. Optionally edit and resubmit

## Notes
- All email actions require human approval
- This is a production system with HITL enforcement
```

**What you do:**
- Review the proposed reply
- Edit if needed
- **Move file to `approved/` to send**
- **Move to `rejected/` to discard**

---

### **STEP 5: Human Reviews & Approves**

**YOUR ACTION REQUIRED!**

**Commands:**
```bash
# 1. Review pending approvals
ls pending_approval/
cat pending_approval/APPROVAL_email_reply_*.md

# 2. Approve (send email)
mv pending_approval/APPROVAL_email_reply_*.md approved/

# OR Reject (discard)
mv pending_approval/APPROVAL_email_reply_*.md rejected/
```

**What happens:**
- File moved to `approved/` → Email MCP sends email
- File moved to `rejected/` → Email discarded

---

### **STEP 6: Email MCP Sends Real Email**

**File:** `mcp_servers/email_mcp.py`

**What it does:**
- Monitors `approved/` folder
- Reads approval files
- Sends emails via Gmail API
- Logs all actions

**Command (automatic or manual):**
```bash
# Automatic (via orchestrator)
python orchestrator.py

# Manual
python -m mcp_servers.email_mcp
```

**Result:**
- Real email sent via Gmail API
- File moved to `done/`
- Log entry created

---

### **STEP 7: Email Sent - File Moved to done/**

**Folder:** `done/`

**File moved:** `done/APPROVAL_email_reply_{timestamp}.md`

**What it means:**
- ✅ Email successfully sent
- ✅ Check your Gmail Sent folder
- ✅ Audit log created

---

## 📁 Folder Structure Summary

```
silver-tier-ai-employee/
├── needs_action/          # ← New emails land here (auto)
│   └── EMAIL_*.md
│
├── plans/                 # ← Processing plans (auto)
│   └── PLAN_*.md
│
├── pending_approval/      # ← YOUR ACTION NEEDED!
│   └── APPROVAL_*.md      #    Review & move to approved/
│
├── approved/              # ← Ready to send (auto)
│   └── APPROVAL_*.md
│
├── rejected/              # ← Discarded emails
│   └── APPROVAL_*.md
│
├── done/                  # ← Completed emails
│   └── APPROVAL_*.md
│
├── logs/
│   ├── gmail_*.log        # Gmail watcher logs
│   ├── email_mcp_*.log    # Email MCP logs
│   └── audit/             # Audit logs
│
└── watchers/
    └── gmail_watcher.py   # Monitors inbox
```

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: New Email Arrives in Gmail                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Gmail Watcher Detects Email                        │
│ File: watchers/gmail_watcher.py                            │
│ Action: Creates EMAIL_*.md in needs_action/                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Orchestrator Creates Plan                          │
│ File: orchestrator.py                                       │
│ Action: Creates PLAN_*.md in plans/                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Approval Request Created                           │
│ Action: Creates APPROVAL_*.md in pending_approval/         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: ⚠️ HUMAN REVIEW (HITL)                             │
│ YOUR ACTION:                                                │
│ - Review: cat pending_approval/APPROVAL_*.md               │
│ - Approve: mv pending_approval/APPROVAL_*.md approved/     │
│ - Reject: mv pending_approval/APPROVAL_*.md rejected/      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Email MCP Sends Email                              │
│ File: mcp_servers/email_mcp.py                             │
│ Action: Sends real email via Gmail API                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Email Sent - Complete                              │
│ Action: File moved to done/                                │
│ Result: Check Gmail Sent folder!                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Quick Reference Commands

### **Monitor Inbox**
```bash
# Start Gmail Watcher
python watchers/gmail_watcher.py
```

### **Check Pending Approvals**
```bash
# List pending
ls -la pending_approval/

# Review content
cat pending_approval/APPROVAL_*.md
```

### **Approve Email**
```bash
# Move to approved (sends email)
mv pending_approval/APPROVAL_*.md approved/
```

### **Reject Email**
```bash
# Move to rejected (discards)
mv pending_approval/APPROVAL_*.md rejected/
```

### **Check Sent Emails**
```bash
# List completed
ls -la done/

# View sent email
cat done/APPROVAL_*.md
```

### **Check Logs**
```bash
# Gmail watcher logs
tail -f logs/gmail_watcher_*.log

# Email MCP logs
tail -f logs/email_mcp_*.log

# Audit logs
cat logs/audit/*.jsonl
```

---

## ✅ HITL (Human-in-the-Loop) Enforcement

**What is HITL?**
- **Human-in-the-Loop** means NO email is sent without your approval
- All outgoing emails require manual review
- You control what gets sent

**How it works:**
1. Incoming email → `needs_action/` (automatic)
2. Reply drafted → `pending_approval/` (automatic)
3. **YOU review** → Approve or Reject (MANUAL)
4. If approved → `approved/` → Email sent (automatic)
5. If rejected → `rejected/` → Email discarded (automatic)

**Why HITL?**
- ✅ Prevents accidental sends
- ✅ Ensures quality control
- ✅ You review all communications
- ✅ AI suggests, human decides

---

## 🎯 Production Usage Example

### **Scenario: Client Email Inquiry**

**1. Client sends email:**
```
From: john@client.com
Subject: AI Automation Pricing
Content: Hi, can you send me your pricing?
```

**2. Watcher detects:**
```bash
# File created: needs_action/EMAIL_19cf3a334af87d68.md
```

**3. You review pending:**
```bash
ls pending_approval/
cat pending_approval/APPROVAL_email_reply_*.md
```

**4. You approve:**
```bash
mv pending_approval/APPROVAL_email_reply_*.md approved/
```

**5. Email sent automatically:**
```bash
# Check done folder
ls done/
# Check Gmail Sent folder
# https://mail.google.com/
```

---

## 📞 Support & Troubleshooting

### **Email not appearing in needs_action/?**
```bash
# Check Gmail Watcher is running
python watchers/gmail_watcher.py

# Check logs
tail -f logs/gmail_watcher_*.log
```

### **Approval not being processed?**
```bash
# Check file is in approved/
ls approved/

# Run orchestrator
python orchestrator.py
```

### **Email not sent?**
```bash
# Check Email MCP logs
tail -f logs/email_mcp_*.log

# Check credentials in .env
cat .env | grep GMAIL
```

---

## ✅ Summary

| Step | Folder | Action | Who |
|------|--------|--------|-----|
| 1. Email arrives | Gmail Inbox | - | External |
| 2. Detected | `needs_action/` | Auto-create | Watcher |
| 3. Plan created | `plans/` | Auto-create | Orchestrator |
| 4. Approval created | `pending_approval/` | Auto-create | Orchestrator |
| 5. **Review** | `pending_approval/` | **Review & Move** | **YOU** ⚠️ |
| 6. Email sent | `approved/` → Gmail | Auto-send | Email MCP |
| 7. Complete | `done/` | Auto-move | Orchestrator |

---

**📧 Gmail automation is now PRODUCTION READY with full HITL enforcement!**
