# 📱 LinkedIn End-to-End Test - Complete Guide

## ⚠️ STEP 0: Authenticate (One-Time Setup)

**RUN THIS FIRST:**

```bash
cd /mnt/e/hackathon-0-ai-employee/silver-tier-ai-employee
source venv/bin/activate
python linkedin_authenticate.py
```

**WHAT TO DO:**

1. **Browser Opens** - Chromium browser will open
2. **LinkedIn Login** - You'll see login page
3. **Enter Credentials** - Your LinkedIn email & password
4. **Complete Verification** - If any 2FA
5. **Wait for Feed** - Make sure you see your LinkedIn feed
6. **Wait 10 seconds** - Let session save
7. **Browser closes** - Authentication complete

**SESSION SAVED TO:**
```
sessions/linkedin/
```

**VALID FOR:** ~30 days

---

## ✅ STEP 1: Create LinkedIn Post

```bash
cat > needs_action/LINKEDIN_E2E_TEST.md << 'EOF'
---
type: linkedin_post_request
topic: End-to-End Test
created: 2026-03-16
---

## Post Content
```
🧪 END-TO-END TEST - LinkedIn Automation

Testing the complete AI Employee Silver Tier workflow:

✅ Watcher monitoring
✅ Approval workflow (HITL)
✅ Browser automation (Playwright)
✅ LinkedIn posting

#Test #Automation #LinkedIn #AI
```
EOF
```

**FILE CREATED:** `needs_action/LINKEDIN_E2E_TEST.md`

---

## ✅ STEP 2: Run LinkedIn Watcher

```bash
python watchers/linkedin_watcher.py
```

**WHAT HAPPENS:**

1. Watcher starts
2. Detects `LINKEDIN_E2E_TEST.md`
3. Creates approval file
4. Logs: "✓ Approval request created"

**PRESS Ctrl+C** to stop watcher after 10 seconds.

---

## ✅ STEP 3: Check Approval Created

```bash
ls -la pending_approval/LINKEDIN_POST_*.md
cat pending_approval/LINKEDIN_POST_*.md | head -30
```

**YOU SHOULD SEE:**

```markdown
---
type: approval_request
action: linkedin_post
created: 2026-03-16T...
status: pending
requires_human_approval: true
---

# LinkedIn Post Approval Request ⚠️ HUMAN-IN-THE-LOOP

## Post Content
```
🧪 END-TO-END TEST - LinkedIn Automation
...
```
```

---

## ✅ STEP 4: Approve Post (HITL)

```bash
# Move to approved (this is the HITL step!)
mv pending_approval/LINKEDIN_POST_*.md approved/

# Verify moved
ls approved/
```

**EXPECTED:**
```
LINKEDIN_POST_20260316_HHMMSS.md
```

---

## ✅ STEP 5: Post to LinkedIn

```bash
python -m skills.linkedin_poster
```

**WHAT HAPPENS:**

1. **Browser Opens** - With your saved session
2. **Navigates to Feed** - `https://www.linkedin.com/feed/`
3. **Clicks "Start a post"** - Opens dialog
4. **Enters Content** - Your post text
5. **Clicks "Post"** - Publishes to LinkedIn
6. **Takes Screenshots** - Saved to `logs/`
7. **Moves to done/** - Complete!

**EXPECTED OUTPUT:**

```
📄 File: LINKEDIN_POST_20260316_HHMMSS.md

📝 Content (xxx chars):
------------------------------------------------------------
🧪 END-TO-END TEST - LinkedIn Automation
...
------------------------------------------------------------

[1/7] Opening browser...
[2/7] Navigating to LinkedIn feed...
    ✓ URL: https://www.linkedin.com/feed/
[3/7] Starting a post...
    ✓ Clicked 'Start a post' button
[4/7] Waiting for post dialog...
    ✓ Post dialog appeared
[5/7] Entering post content...
    ✓ Content entered via role
[6/7] Waiting for Post button...
    ✓ Post button visible
[7/7] Clicking Post button...
    ✓ Post button clicked
    ⏳ Waiting for post to publish...

✅ DONE!
   Check: https://www.linkedin.com/feed/

✓ Moved to: done/LINKEDIN_POST_20260316_HHMMSS.md
```

---

## ✅ STEP 6: Verify on LinkedIn

**GO TO:** https://www.linkedin.com/feed/

**LOOK FOR:**

> 🧪 END-TO-END TEST - LinkedIn Automation
> 
> Testing the complete AI Employee Silver Tier workflow...

**CHECK:**
- ✅ Post visible on your feed
- ✅ Content matches what you wrote
- ✅ Hashtags included
- ✅ Posted just now

---

## ✅ STEP 7: Verify Files

```bash
# Check moved to done/
ls -la done/LINKEDIN_*.md

# Check logs
ls -la logs/li_*.png

# Check audit trail
cat logs/linkedin_watcher_*.log | tail -20
```

**EXPECTED:**

```
done/
  └── LINKEDIN_POST_20260316_HHMMSS.md  ← Posted successfully

logs/
  ├── li_feed_HHMMSS.png      ← Feed screenshot
  ├── li_dialog_HHMMSS.png    ← Dialog screenshot
  ├── li_content_HHMMSS.png   ← Content entered
  └── li_posted_HHMMSS.png    ← Post published
```

---

## 📊 COMPLETE WORKFLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 0: Authenticate (One-time)                            │
│ python linkedin_authenticate.py                            │
│ → Session saved to sessions/linkedin/                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Create Post                                        │
│ needs_action/LINKEDIN_E2E_TEST.md                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Watcher Detects                                    │
│ python watchers/linkedin_watcher.py                        │
│ → Creates approval file                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Approval Created                                   │
│ pending_approval/LINKEDIN_POST_*.md                        │
│ ⚠️ WAITING FOR HUMAN APPROVAL                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Human Approves (HITL) ⚠️                           │
│ mv pending_approval/*.md approved/                         │
│ ← YOU DO THIS MANUALLY                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Post to LinkedIn                                   │
│ python -m skills.linkedin_poster                           │
│ → Browser opens                                            │
│ → Navigates to feed                                        │
│ → Clicks "Start a post"                                    │
│ → Enters content                                           │
│ → Clicks "Post"                                            │
│ → Published to LinkedIn!                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Verify                                             │
│ → Check LinkedIn feed                                      │
│ → See your post                                            │
│ → File moved to done/                                      │
│ → Screenshots in logs/                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 SUCCESS CRITERIA

**ALL MUST BE TRUE:**

- [ ] ✅ Authenticated (session saved)
- [ ] ✅ Post file created in `needs_action/`
- [ ] ✅ Approval created in `pending_approval/`
- [ ] ✅ Approved (moved to `approved/`)
- [ ] ✅ Browser opened and posted
- [ ] ✅ Post visible on LinkedIn feed
- [ ] ✅ File moved to `done/`
- [ ] ✅ Screenshots in `logs/`

---

## 🔧 TROUBLESHOOTING

### **"Not logged in"**
```bash
# Re-authenticate
python linkedin_authenticate.py
# Log in again
```

### **"Post button not found"**
- Make sure you're logged in
- Check browser opened
- Verify on LinkedIn feed
- Check `logs/li_*.png` screenshots

### **"Session expired"**
```bash
# Clear and re-authenticate
rm -rf sessions/linkedin/Default
python linkedin_authenticate.py
```

### **"Post not appearing on LinkedIn"**
- Check LinkedIn feed: https://www.linkedin.com/feed/
- Check screenshots in `logs/`
- Check `logs/linkedin_test.log` for errors

---

## ✅ END-TO-END TEST COMPLETE!

When all steps pass, you have verified:

1. ✅ **LinkedIn Authentication** - Browser login works
2. ✅ **Watcher** - Detects post requests
3. ✅ **Approval Workflow** - HITL enforcement
4. ✅ **Browser Automation** - Playwright posting
5. ✅ **LinkedIn API** - Post published
6. ✅ **Audit Trail** - All actions logged

**🎉 LinkedIn Automation is PRODUCTION READY!**

---

## 📋 QUICK REFERENCE

```bash
# Authenticate (one-time)
python linkedin_authenticate.py

# Create post
nano needs_action/LINKEDIN_POST.md

# Run watcher
python watchers/linkedin_watcher.py

# Approve
mv pending_approval/*.md approved/

# Post
python -m skills.linkedin_poster

# Verify
# https://www.linkedin.com/feed/
```

---

**Ready to test? Run Step 0 now!** 📱✅
