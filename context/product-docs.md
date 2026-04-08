# TechCorp Platform — Product Documentation

## Table of Contents
1. Getting Started
2. Account Management
3. Project Management
4. Task Management
5. Team Collaboration
6. Workflow Automation
7. API Reference
8. Billing & Plans
9. Troubleshooting
10. Mobile Apps

---

## 1. Getting Started

### Creating an Account
1. Visit techcorp.io/signup
2. Enter your work email and create a password
3. Verify your email via the confirmation link
4. Complete the onboarding wizard (takes 2 minutes)
5. Your workspace is ready immediately

### Setting Up Your Workspace
1. **Name your workspace** — This is your team's shared environment
2. **Invite team members** — Via email or shareable invite link
3. **Create your first project** — Click "+ New Project" from the dashboard
4. **Configure settings** — Go to Settings → Workspace to customize

### Quick Start Checklist
- [ ] Create account and verify email
- [ ] Set up workspace name and logo
- [ ] Invite at least one team member
- [ ] Create your first project
- [ ] Add your first task
- [ ] Explore the dashboard

---

## 2. Account Management

### Resetting Your Password
1. Go to techcorp.io/login
2. Click "Forgot Password?"
3. Enter your email address
4. Check your inbox for the reset link (valid for 1 hour)
5. Click the link and set a new password
6. Password requirements: minimum 8 characters, 1 uppercase, 1 number

**Note:** If you don't receive the email within 5 minutes, check your spam folder.

### Updating Your Profile
1. Click your avatar in the top-right corner
2. Select "Profile Settings"
3. Update name, avatar, timezone, or notification preferences
4. Click "Save Changes"

### Two-Factor Authentication (2FA)
1. Go to Settings → Security
2. Click "Enable Two-Factor Authentication"
3. Scan the QR code with your authenticator app (Google Authenticator, Authy)
4. Enter the 6-digit code to verify
5. Save your backup codes in a secure location

### Deleting Your Account
1. Go to Settings → Account
2. Scroll to "Danger Zone"
3. Click "Delete Account"
4. Confirm by typing your email address
5. **Warning:** This action is irreversible. All your data will be permanently deleted.

---

## 3. Project Management

### Creating a Project
1. From the dashboard, click "+ New Project"
2. Choose a template or start from scratch
3. Name your project and add a description
4. Set privacy: Public (workspace-wide) or Private (invite-only)
5. Click "Create Project"

### Project Views
- **Board View:** Kanban-style columns for visual task management
- **List View:** Spreadsheet-like list for detailed task tracking
- **Timeline View:** Gantt chart for project planning and dependencies
- **Calendar View:** Tasks displayed on a calendar by due date

### Project Templates
| Template | Best For |
|----------|----------|
| Sprint Planning | Agile teams running 2-week sprints |
| Content Calendar | Marketing teams planning content |
| Bug Tracker | Development teams tracking issues |
| Event Planning | Organizing events and milestones |
| CRM Pipeline | Sales teams managing leads |
| Onboarding | HR teams for new employee onboarding |

### Archiving a Project
1. Open the project
2. Click the project name dropdown → Project Settings
3. Click "Archive Project"
4. Archived projects are hidden from the dashboard but can be restored

---

## 4. Task Management

### Creating a Task
1. Open any project
2. Click "+ Add Task" or the "+" button in any column
3. Enter a task title and press Enter
4. Click the task to add details: description, assignee, due date, labels, attachments

### Task Fields
| Field | Description |
|-------|-------------|
| Title | Brief description of the task |
| Description | Detailed instructions (supports Markdown) |
| Assignee | Team member responsible for the task |
| Due Date | When the task should be completed |
| Priority | Low, Medium, High, Urgent |
| Labels | Color-coded tags for categorization |
| Attachments | Files up to 100MB each |
| Subtasks | Break tasks into smaller steps |
| Dependencies | Tasks that must be completed first |

### Task Status Workflow
```
To Do → In Progress → In Review → Done
```

Customize this in Project Settings → Workflow.

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| N | Create new task |
| / | Search tasks |
| Esc | Close task detail |
| ← → | Navigate between tasks |
| Del | Delete selected task |
| Space | Toggle task completion |

---

## 5. Team Collaboration

### Inviting Team Members
1. Go to Settings → Team Members
2. Click "Invite Members"
3. Enter email addresses (comma-separated for multiple)
4. Select role: Member (full access) or Viewer (read-only)
5. Click "Send Invites"

### Commenting on Tasks
1. Open a task
2. Scroll to the Comments section
3. Type your comment (supports @mentions)
4. Press Enter or click "Send"
5. Attach files by dragging them into the comment area

### @Mentions
- Type @ followed by a name to notify a team member
- The mentioned person receives a notification (email + in-app)
- Use @here to notify all project members

### File Sharing
- Drag and drop files into tasks or comments
- Supported formats: images, PDFs, documents, spreadsheets
- Maximum file size: 100MB per file
- Total storage: varies by plan (1GB Starter, 50GB Professional, Unlimited Enterprise)

---

## 6. Workflow Automation

### Creating an Automation Rule
1. Go to Project Settings → Automation
2. Click "+ New Rule"
3. Choose a trigger:
   - Task created
   - Task assigned
   - Due date approaching
   - Task completed
   - Status changed
   - Comment added
4. Choose an action:
   - Assign to team member
   - Set due date
   - Add label
   - Move to column
   - Send notification
   - Create subtask
5. Click "Save Rule"

### Built-in Automation
| Automation | What It Does |
|-----------|-------------|
| Auto-assign on creation | Assigns new tasks to a specific person |
| Due date reminders | Sends notification 24h before due date |
| Auto-archive completed | Moves completed tasks to archive after 7 days |
| Label on status change | Automatically applies labels when status changes |
| Escalate overdue tasks | Notifies manager when task is 3+ days overdue |

### Automation Limits
- Starter plan: 100 automation runs/month
- Professional plan: 10,000 automation runs/month
- Enterprise plan: Unlimited automation runs

---

## 7. API Reference

### Base URL
```
https://api.techcorp.io/v2
```

### Authentication
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_API_TOKEN
```

### Generating an API Token
1. Go to Settings → API Keys
2. Click "Generate New Token"
3. Give it a descriptive name
4. Choose scope: Read-only or Read/Write
5. Copy the token immediately — it won't be shown again

### Rate Limits
| Plan | Requests/Hour | Burst Limit |
|------|--------------|-------------|
| Starter | 100 | 20 |
| Professional | 1,000 | 200 |
| Enterprise | 10,000 | 2,000 |

### Key Endpoints
```
GET    /projects              — List all projects
POST   /projects              — Create a project
GET    /projects/{id}         — Get project details
GET    /projects/{id}/tasks   — List project tasks
POST   /projects/{id}/tasks   — Create a task
GET    /tasks/{id}            — Get task details
PUT    /tasks/{id}            — Update a task
DELETE /tasks/{id}            — Delete a task
GET    /users                 — List team members
GET    /me                    — Get current user info
POST   /webhooks              — Create a webhook
GET    /webhooks              — List webhooks
```

### Webhooks
1. Go to Settings → Webhooks
2. Click "Add Webhook"
3. Enter your endpoint URL
4. Select events to subscribe to
5. TechCorp will POST JSON payloads to your URL on events

### Error Codes
| Code | Meaning |
|------|--------|
| 400 | Bad Request — Invalid parameters |
| 401 | Unauthorized — Invalid or missing API token |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource doesn't exist |
| 429 | Too Many Requests — Rate limit exceeded |
| 500 | Internal Server Error — Our problem |

---

## 8. Billing & Plans

### Available Plans

#### Starter (Free)
- Up to 5 users
- 1GB storage
- Basic project views (Board, List)
- Email support
- Core integrations

#### Professional ($29/user/month, billed annually)
- Unlimited users
- 50GB storage
- All project views + Timeline
- Workflow automation (10,000 runs/month)
- API access
- Priority email + chat support
- 200+ integrations

#### Enterprise ($79/user/month, billed annually)
- Everything in Professional
- Unlimited storage
- Unlimited automation
- SSO/SAML
- Custom integrations
- 99.9% SLA guarantee
- Dedicated account manager
- Phone support
- Custom onboarding

### Upgrading Your Plan
1. Go to Settings → Billing
2. Click "Upgrade Plan"
3. Select your desired plan
4. Enter payment details (credit card or invoice)
5. Changes take effect immediately

### Downgrading Your Plan
1. Go to Settings → Billing
2. Click "Change Plan"
3. Select the lower-tier plan
4. Changes take effect at the end of your billing cycle
5. **Note:** If you exceed the lower plan's limits, some features may be restricted

### Canceling Your Subscription
1. Go to Settings → Billing
2. Click "Cancel Subscription"
3. Select a reason for cancellation
4. Confirm cancellation
5. You retain access until the end of your billing period

### Refund Policy
- Annual plans: Prorated refund within 30 days of purchase
- Monthly plans: No refunds for partial months
- Enterprise plans: Per contract terms

### Payment Methods
- Credit/Debit Card (Visa, Mastercard, Amex)
- Bank Transfer (Enterprise only)
- Purchase Order (Enterprise only)

---

## 9. Troubleshooting

### Common Issues

#### "I can't log in"
1. Verify your email address is correct
2. Try resetting your password
3. Clear browser cache and cookies
4. Try an incognito/private browsing window
5. Check if the service is down at status.techcorp.io

#### "Tasks aren't loading"
1. Check your internet connection
2. Refresh the page (Ctrl+R / Cmd+R)
3. Clear browser cache
4. Try a different browser
5. Check status.techcorp.io for outages

#### "I'm not receiving notifications"
1. Go to Settings → Notifications
2. Verify notification preferences are enabled
3. Check your email spam folder
4. Ensure your email address is correct in your profile
5. Check if notifications are paused (Do Not Disturb mode)

#### "File upload is failing"
1. Check file size (max 100MB per file)
2. Verify file format is supported
3. Check your available storage in Settings → Billing
4. Try uploading a smaller file to test
5. Check your internet connection

#### "API requests are returning 429"
1. You've exceeded your rate limit
2. Wait for the rate limit window to reset (1 hour)
3. Implement exponential backoff in your code
4. Consider upgrading your plan for higher limits

### System Status
Check real-time system status at **status.techcorp.io**

Subscribe to status updates:
- Email notifications
- SMS alerts
- Slack webhook
- RSS feed

---

## 10. Mobile Apps

### Download
- **iOS:** App Store — search "TechCorp Platform"
- **Android:** Google Play — search "TechCorp Platform"

### Features Available on Mobile
- View and edit tasks
- Comment on tasks
- Receive push notifications
- View project boards and lists
- Upload photos from your device
- Quick task creation via widget

### Mobile-Specific Features
- **Quick Capture Widget:** Add tasks from your home screen without opening the app
- **Camera Attachments:** Take photos and attach directly to tasks
- **Offline Mode:** View recently accessed projects without internet (changes sync when connected)
- **Biometric Login:** Use Face ID or fingerprint to log in

### Mobile Push Notifications
Configure in the app: Settings → Notifications
- Task assigned to you
- Task due soon
- Someone comments on your task
- @Mentions
- Project updates
