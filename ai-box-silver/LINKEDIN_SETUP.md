# 📱 LinkedIn Automation - Setup & Usage Guide

## ⚠️ IMPORTANT: Authentication Required

LinkedIn requires you to log in via browser before automation can work. This is a **one-time setup**.

---

## 🔐 STEP 1: Authenticate with LinkedIn

### **Run the Authentication Script**

```bash
cd /mnt/e/hackathon-0-ai-employee/silver-tier-ai-employee
source venv/bin/activate
python -m skills.linkedin_poster
```

### **What Happens:**

1. **Browser Opens** - Chromium browser will open
2. **LinkedIn Login Page** - You'll see LinkedIn login
3. **Sign In** - Enter your LinkedIn credentials
4. **Stay on Feed** - Make sure you're on `https://www.linkedin.com/feed/`
5. **Wait 10 seconds** - Let the session save
6. **Close browser** - Script will complete

### **Session Saved:**

Your LinkedIn session is saved to:
```
sessions/linkedin/
```

This session will be reused for future posts (valid for ~30 days).

---

## 📋 STEP 2: Create LinkedIn Post Request

### **Create File in needs_action/**

```bash
nano needs_action/LINKEDIN_MYPOST.md
```

### **Content Format:**

```markdown
---
type: linkedin_post_request
topic: Your Topic Here
created: 2026-03-16
---

## Post Content
```
Your LinkedIn post content here...

Include hashtags: #AI #Automation #LinkedIn
```
```

---

## ✅ STEP 3: Run LinkedIn Watcher

```bash
python watchers/linkedin_watcher.py
```

**What it does:**
- Detects your post request
- Creates approval file in `pending_approval/`

---

## 🔒 STEP 4: Approve Post (HITL)

### **Review Approval:**

```bash
cat pending_approval/LINKEDIN_POST_*.md
```

### **Approve:**

```bash
mv pending_approval/LINKEDIN_POST_*.md approved/
```

---

## 🚀 STEP 5: Post to LinkedIn

```bash
python -m skills.linkedin_poster
```

**What happens:**
1. Browser opens with your saved session
2. Navigates to LinkedIn feed
3. Clicks "Start a post"
4. Enters your content
5. Clicks "Post"
6. Post published to LinkedIn!

---

## 📁 Complete Workflow

```
1. Create post → needs_action/LINKEDIN_*.md
   ↓
2. Watcher detects → Creates approval
   ↓
3. Approval created → pending_approval/LINKEDIN_POST_*.md
   ↓
4. You approve → Move to approved/
   ↓
5. Poster runs → Posts to LinkedIn
   ↓
6. Complete → Moved to done/
```

---

## 🎯 Quick Commands

| Action | Command |
|--------|---------|
| **Authenticate** | First time only - browser opens |
| **Create post** | `nano needs_action/LINKEDIN_POST.md` |
| **Start watcher** | `python watchers/linkedin_watcher.py` |
| **Check pending** | `ls pending_approval/` |
| **Approve** | `mv pending_approval/*.md approved/` |
| **Post** | `python -m skills.linkedin_poster` |
| **Check posted** | `ls done/` |

---

## ✅ Silver Tier Requirements Met

- ✅ **LinkedIn Watcher** - Monitors post requests
- ✅ **Approval Workflow** - HITL enforcement
- ✅ **Browser Automation** - Playwright with stable selectors
- ✅ **Auto Posting** - Once approved, posts automatically
- ✅ **Session Persistence** - Login once, reuse session
- ✅ **Audit Logging** - All actions logged

---

## 🔧 Troubleshooting

### **"Not logged in" error:**
```bash
# Clear session and re-authenticate
rm -rf sessions/linkedin/Default
python -m skills.linkedin_poster
# Browser opens - log in again
```

### **"Post button not found":**
- Make sure you're logged in
- Check browser window opened
- Verify you're on LinkedIn feed
- Check logs/linkedin_test.log for details

### **"Session expired":**
```bash
# Re-authenticate
rm -rf sessions/linkedin/Default
python -m skills.linkedin_poster
```

---

## 📊 Test Your Setup

```bash
# 1. Create test post
cat > needs_action/LINKEDIN_TEST.md << 'EOF'
---
type: linkedin_post_request
topic: Test Post
---

## Post Content
```
Testing LinkedIn automation! 🚀

#Test #LinkedIn #Automation
```
EOF

# 2. Run watcher
python watchers/linkedin_watcher.py

# 3. Approve
mv pending_approval/LINKEDIN_POST_*.md approved/

# 4. Post
python -m skills.linkedin_poster

# 5. Check LinkedIn
# https://www.linkedin.com/feed/
```

---

## ✅ Ready for Production!

Once authenticated, the workflow is:
1. Create post in `needs_action/`
2. Watcher creates approval
3. You approve (move to `approved/`)
4. Poster publishes to LinkedIn

**Fully automated with HITL enforcement!** 📱✅
