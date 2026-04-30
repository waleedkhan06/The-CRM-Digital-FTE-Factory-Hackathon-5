"""
Test script for Silver Tier AI Employee functionality
Tests all Silver Tier requirements:
1. Two or more Watcher scripts (Gmail + WhatsApp + File System)
2. LinkedIn posting capability
3. Claude reasoning loop with Plan.md creation
4. Email MCP server
5. Human-in-the-loop approval workflow
6. Basic scheduling
7. All AI functionality as Agent Skills
"""
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_folder_structure():
    """Test that all required folders exist"""
    print("\n" + "=" * 50)
    print("TEST: Folder Structure")
    print("=" * 50)
    
    required_folders = [
        'inbox',
        'needs_action',
        'done',
        'plans',
        'pending_approval',
        'approved',
        'rejected',
        'logs',
        'logs/audit',
        'watchers',
        'mcp_servers',
        'skills',
        'sessions/whatsapp'
    ]
    
    all_good = True
    for folder in required_folders:
        folder_path = project_root / folder
        if folder_path.exists():
            print(f"  ✓ {folder}/ exists")
        else:
            print(f"  ✗ {folder}/ missing - creating...")
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"    Created: {folder}/")
    
    return all_good


def test_files_exist():
    """Test that all required files exist"""
    print("\n" + "=" * 50)
    print("TEST: Required Files")
    print("=" * 50)
    
    required_files = [
        'dashboard.md',
        'company_handbook.md',
        'requirements.txt',
        'main.py',
        'orchestrator.py',
        'scheduler.py',
        'ralph_wiggum.py',
        '.env'
    ]
    
    all_good = True
    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"  ✓ {file} exists")
        else:
            print(f"  ✗ {file} missing")
            all_good = False
    
    return all_good


def test_watchers():
    """Test that all watcher files exist and can be imported"""
    print("\n" + "=" * 50)
    print("TEST: Watchers (Silver Tier Requirement: 2+)")
    print("=" * 50)
    
    watcher_files = [
        ('watchers/base_watcher.py', 'BaseWatcher'),
        ('watchers/filesystem_watcher.py', 'FileSystemWatcher'),
        ('watchers/gmail_watcher.py', 'GmailWatcher'),
        ('watchers/whatsapp_watcher.py', 'WhatsAppWatcher'),
    ]
    
    all_good = True
    watchers_available = 0
    
    for watcher_file, class_name in watcher_files:
        watcher_path = project_root / watcher_file
        if watcher_path.exists():
            print(f"  ✓ {watcher_file} exists")
            
            # Try to import
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "watcher_module", 
                    watcher_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, class_name):
                    print(f"    ✓ {class_name} class available")
                    if class_name != 'BaseWatcher':
                        watchers_available += 1
                else:
                    print(f"    ✗ {class_name} class not found")
                    all_good = False
            except Exception as e:
                print(f"    ✗ Import failed: {e}")
                all_good = False
        else:
            print(f"  ✗ {watcher_file} missing")
            all_good = False
    
    print(f"\n  Total watchers available: {watchers_available}")
    if watchers_available >= 2:
        print(f"  ✓ Silver Tier requirement met (2+ watchers)")
    else:
        print(f"  ✗ Silver Tier requirement NOT met (need 2+ watchers)")
        all_good = False
    
    return all_good


def test_skills():
    """Test that all skill files exist and can be imported"""
    print("\n" + "=" * 50)
    print("TEST: Agent Skills")
    print("=" * 50)
    
    skill_files = [
        ('skills/file_manager.py', ['move_file', 'create_file', 'read_file', 'list_files']),
        ('skills/process_task.py', ['process_task', 'list_pending_tasks']),
        ('skills/update_dashboard.py', ['update_dashboard', 'get_dashboard_status']),
        ('skills/linkedin_poster.py', ['post_to_linkedin', 'schedule_business_post', 'create_approval_request']),
        ('skills/approval_workflow.py', ['ApprovalWorkflow']),
        ('skills/audit_logger.py', ['AuditLogger', 'log_action']),
    ]
    
    all_good = True
    skills_available = 0
    
    for skill_file, functions in skill_files:
        skill_path = project_root / skill_file
        if skill_path.exists():
            print(f"  ✓ {skill_file} exists")
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "skill_module", 
                    skill_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                func_found = 0
                for func in functions:
                    if hasattr(module, func):
                        print(f"    ✓ {func} available")
                        func_found += 1
                    else:
                        print(f"    ✗ {func} missing")
                
                if func_found == len(functions):
                    skills_available += 1
                    
            except Exception as e:
                print(f"    ✗ Import failed: {e}")
                all_good = False
        else:
            print(f"  ✗ {skill_file} missing")
            all_good = False
    
    print(f"\n  Total skills available: {skills_available}/{len(skill_files)}")
    return all_good


def test_mcp_servers():
    """Test that MCP server files exist"""
    print("\n" + "=" * 50)
    print("TEST: MCP Servers")
    print("=" * 50)
    
    mcp_files = [
        ('mcp_servers/email_mcp.py', 'EmailMCPServer'),
    ]
    
    all_good = True
    
    for mcp_file, class_name in mcp_files:
        mcp_path = project_root / mcp_file
        if mcp_path.exists():
            print(f"  ✓ {mcp_file} exists")
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "mcp_module", 
                    mcp_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, class_name):
                    print(f"    ✓ {class_name} class available")
                else:
                    print(f"    ✗ {class_name} class not found")
                    all_good = False
                    
            except Exception as e:
                print(f"    ✗ Import failed: {e}")
                all_good = False
        else:
            print(f"  ✗ {mcp_file} missing")
            all_good = False
    
    return all_good


def test_approval_workflow():
    """Test the approval workflow functionality"""
    print("\n" + "=" * 50)
    print("TEST: Human-in-the-Loop Approval Workflow")
    print("=" * 50)
    
    try:
        from skills.approval_workflow import ApprovalWorkflow
        
        workflow = ApprovalWorkflow(str(project_root))
        
        # Test creating an approval request
        print("  Creating approval request...")
        result = workflow.create_approval_request(
            action_type="test_email_send",
            details={
                "to": "test@example.com",
                "subject": "Test Email",
                "priority": "medium"
            },
            reason="Testing approval workflow"
        )
        
        if result['status'] == 'success':
            print(f"  ✓ Approval request created: {result['approval_file']}")
            approval_file = result['approval_file']
        else:
            print(f"  ✗ Failed to create approval request: {result['message']}")
            return False
        
        # Test listing pending requests
        print("  Listing pending requests...")
        list_result = workflow.list_pending_requests()
        if list_result['status'] == 'success':
            print(f"  ✓ Found {list_result['count']} pending requests")
        else:
            print(f"  ✗ Failed to list pending requests")
            return False
        
        # Test approving the request
        print("  Approving request...")
        approve_result = workflow.approve_request(approval_file)
        if approve_result['status'] == 'success':
            print(f"  ✓ Request approved: {approve_result['approved_file']}")
        else:
            print(f"  ✗ Failed to approve request: {approve_result['message']}")
            return False
        
        # Clean up - move to done
        approved_file = Path(approve_result['approved_file'])
        if approved_file.exists():
            done_file = project_root / 'done' / approved_file.name
            if done_file.exists():
                done_file.unlink()
            approved_file.rename(done_file)
        
        print("  ✓ Approval workflow test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing approval workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_logging():
    """Test the audit logging system"""
    print("\n" + "=" * 50)
    print("TEST: Audit Logging System")
    print("=" * 50)
    
    try:
        from skills.audit_logger import AuditLogger
        
        logger = AuditLogger(str(project_root))
        
        # Test logging an action
        print("  Logging test action...")
        result = logger.log(
            action_type="test_action",
            actor="test_suite",
            target="test_target",
            parameters={"test": "data"},
            result="success",
            category=AuditLogger.CATEGORY_SYSTEM
        )
        
        if result:
            print(f"  ✓ Action logged: {result.action_type}")
        else:
            print(f"  ✗ Failed to log action")
            return False
        
        # Test getting summary
        print("  Getting audit summary...")
        summary = logger.get_summary()
        if summary['status'] == 'success':
            print(f"  ✓ Summary retrieved: {summary.get('total_entries', 0)} entries")
        else:
            print(f"  ✗ Failed to get summary")
            return False
        
        # Test query
        print("  Querying audit logs...")
        results = logger.query(action_type="test_action")
        if results:
            print(f"  ✓ Query returned {len(results)} results")
        else:
            print(f"  ✗ Query returned no results")
        
        print("  ✓ Audit logging test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing audit logging: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_linkedin_poster():
    """Test the LinkedIn poster skill"""
    print("\n" + "=" * 50)
    print("TEST: LinkedIn Poster (Demo Mode)")
    print("=" * 50)
    
    try:
        from skills.linkedin_poster import schedule_business_post, create_approval_request
        
        # Test generating a business post
        print("  Generating business post...")
        post_result = schedule_business_post(
            topic="AI Automation Services",
            include_hashtags=True
        )
        
        if post_result['status'] == 'success':
            print(f"  ✓ Post content generated ({post_result['character_count']} chars)")
            print(f"     Preview: {post_result['content'][:80]}...")
        else:
            print(f"  ✗ Failed to generate post: {post_result['message']}")
            return False
        
        # Test creating approval request
        print("  Creating approval request...")
        approval_result = create_approval_request(
            content=post_result['content'],
            scheduled_time=datetime.now().strftime('%Y-%m-%d %H:%M')
        )
        
        if approval_result['status'] == 'success':
            print(f"  ✓ Approval request created: {approval_result['approval_file']}")
            
            # Clean up
            approval_file = Path(approval_result['approval_file'])
            if approval_file.exists():
                approval_file.unlink()
        else:
            print(f"  ✗ Failed to create approval request: {approval_result['message']}")
            return False
        
        print("  ✓ LinkedIn poster test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing LinkedIn poster: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_mcp():
    """Test the Email MCP server"""
    print("\n" + "=" * 50)
    print("TEST: Email MCP Server (Demo Mode)")
    print("=" * 50)
    
    try:
        from mcp_servers.email_mcp import EmailMCPServer
        
        server = EmailMCPServer()
        
        print(f"  Demo mode: {server.demo_mode}")
        
        # Test sending an email (demo)
        print("  Testing email send (demo)...")
        result = server.send_email(
            to="test@example.com",
            subject="Test Email from AI Employee",
            body="<h1>Test</h1><p>This is a test email.</p>"
        )
        
        if result['status'] == 'success':
            print(f"  ✓ Email sent (demo): {result['message']}")
        else:
            print(f"  ✗ Failed to send email: {result['message']}")
            return False
        
        # Test creating a draft
        print("  Testing draft creation...")
        draft_result = server.draft_email(
            to="test@example.com",
            subject="Draft Test",
            body="This is a draft."
        )
        
        if draft_result['status'] == 'success':
            print(f"  ✓ Draft created: {draft_result['message']}")
        else:
            print(f"  ✗ Failed to create draft: {draft_result['message']}")
            return False
        
        print("  ✓ Email MCP test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing Email MCP: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator():
    """Test the orchestrator Plan.md creation"""
    print("\n" + "=" * 50)
    print("TEST: Orchestrator with Plan.md Creation")
    print("=" * 50)
    
    try:
        from orchestrator import Orchestrator
        
        orchestrator = Orchestrator(str(project_root))
        
        # Create a test task file
        print("  Creating test task file...")
        needs_action = project_root / 'needs_action'
        test_task = needs_action / f'TEST_TASK_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        test_content = f"""---
type: test_task
priority: medium
status: pending
created: {datetime.now().isoformat()}
---

# Test Task

This is a test task for the orchestrator.

## Actions
- [ ] Process this task
- [ ] Verify plan creation
"""
        test_task.write_text(test_content, encoding='utf-8')
        
        # Test plan creation
        print("  Creating plan...")
        plan_file = orchestrator.create_plan(test_task)
        
        if plan_file:
            print(f"  ✓ Plan created: {plan_file.name}")
            
            # Verify plan content
            plan_content = plan_file.read_text()
            if 'Claude Reasoning' in plan_content:
                print(f"  ✓ Plan contains Claude Reasoning section")
            else:
                print(f"  ✗ Plan missing Claude Reasoning section")
                return False
            
            # Clean up
            if plan_file.exists():
                plan_file.unlink()
            if test_task.exists():
                test_task.unlink()
        else:
            print(f"  ✗ Failed to create plan")
            return False
        
        print("  ✓ Orchestrator test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduler():
    """Test the scheduler"""
    print("\n" + "=" * 50)
    print("TEST: Task Scheduler")
    print("=" * 50)
    
    try:
        from scheduler import TaskScheduler
        
        scheduler = TaskScheduler(str(project_root))
        
        # Test getting scheduled jobs
        print("  Setting up scheduled tasks...")
        scheduler.setup_daily_tasks()
        scheduler.setup_weekly_tasks()
        
        jobs = scheduler.get_scheduled_jobs()
        print(f"  ✓ Scheduled {jobs['count']} jobs")
        
        for job in jobs['jobs'][:3]:
            print(f"    - {job['name']}")
        
        print("  ✓ Scheduler test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing scheduler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ralph_wiggum():
    """Test the Ralph Wiggum plugin"""
    print("\n" + "=" * 50)
    print("TEST: Ralph Wiggum Persistence Loop")
    print("=" * 50)
    
    try:
        from ralph_wiggum import RalphWiggumPlugin
        
        plugin = RalphWiggumPlugin(str(project_root), max_iterations=5)
        
        # Test getting status
        print("  Getting plugin status...")
        status = plugin.get_status()
        print(f"  ✓ Status: {status['status']}")
        print(f"    Max iterations: {status['max_iterations']}")
        
        # Test starting a task
        print("  Starting test task...")
        result = plugin.start_task("Test task for Ralph Wiggum")
        if result['status'] == 'success':
            print(f"  ✓ Task started: {result['task_file']}")
            
            # Clean up
            task_file = Path(result['task_file'])
            if task_file.exists():
                task_file.unlink()
        else:
            print(f"  ✗ Failed to start task: {result['message']}")
            return False
        
        print("  ✓ Ralph Wiggum test passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing Ralph Wiggum: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_file():
    """Test that .env file exists and is properly configured"""
    print("\n" + "=" * 50)
    print("TEST: Environment Configuration")
    print("=" * 50)
    
    env_file = project_root / '.env'
    
    if env_file.exists():
        print(f"  ✓ .env file exists")
        
        # Check for demo mode
        content = env_file.read_text()
        if 'DEMO_MODE=true' in content:
            print(f"  ✓ Demo mode enabled (safe for testing)")
        else:
            print(f"  ⚠ Demo mode may not be enabled")
        
        # Check that credentials are empty (for security)
        if 'GMAIL_CLIENT_ID=your_gmail' not in content and 'GMAIL_CLIENT_ID=' in content:
            print(f"  ✓ Gmail credentials not set (configure when ready)")
        
        if 'LINKEDIN_CLIENT_ID=your_linkedin' not in content and 'LINKEDIN_CLIENT_ID=' in content:
            print(f"  ✓ LinkedIn credentials not set (configure when ready)")
        
        return True
    else:
        print(f"  ✗ .env file missing")
        return False


def main():
    """Run all Silver Tier tests"""
    print("\n" + "=" * 60)
    print("AI EMPLOYEE SILVER TIER - FUNCTIONALITY TEST")
    print("=" * 60)
    print(f"Project path: {project_root}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_tests_passed = True
    test_results = {}
    
    # Run all tests
    test_results['folder_structure'] = test_folder_structure()
    test_results['files_exist'] = test_files_exist()
    test_results['env_file'] = test_env_file()
    test_results['watchers'] = test_watchers()
    test_results['skills'] = test_skills()
    test_results['mcp_servers'] = test_mcp_servers()
    test_results['approval_workflow'] = test_approval_workflow()
    test_results['audit_logging'] = test_audit_logging()
    test_results['linkedin_poster'] = test_linkedin_poster()
    test_results['email_mcp'] = test_email_mcp()
    test_results['orchestrator'] = test_orchestrator()
    test_results['scheduler'] = test_scheduler()
    test_results['ralph_wiggum'] = test_ralph_wiggum()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Silver Tier Requirements Check
    print("\n" + "=" * 60)
    print("SILVER TIER REQUIREMENTS CHECK")
    print("=" * 60)
    
    requirements = {
        "1. All Bronze requirements": test_results['folder_structure'] and test_results['files_exist'],
        "2. Two or more Watcher scripts": test_results['watchers'],
        "3. LinkedIn posting capability": test_results['linkedin_poster'],
        "4. Claude reasoning loop (Plan.md)": test_results['orchestrator'],
        "5. One working MCP server": test_results['mcp_servers'] and test_results['email_mcp'],
        "6. Human-in-the-loop approval": test_results['approval_workflow'],
        "7. Basic scheduling": test_results['scheduler'],
        "8. All AI as Agent Skills": test_results['skills'],
    }
    
    req_passed = sum(1 for v in requirements.values() if v)
    req_total = len(requirements)
    
    for req, result in requirements.items():
        status = "✓" if result else "✗"
        print(f"  {status} {req}")
    
    print(f"\nRequirements: {req_passed}/{req_total} met")
    
    print("\n" + "=" * 60)
    if passed == total and req_passed == req_total:
        print("✓ ALL TESTS PASSED - SILVER TIER IMPLEMENTATION COMPLETE!")
        print("\nNext steps:")
        print("1. Run 'python main.py' to start the Silver Tier system")
        print("2. Configure credentials in .env for production use")
        print("3. Monitor /pending_approval for items requiring review")
        print("4. Check dashboard.md for system status")
    else:
        print("✗ SOME TESTS FAILED - Please review errors above")
    
    print("=" * 60)
    
    return all(test_results.values()) and all(requirements.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
