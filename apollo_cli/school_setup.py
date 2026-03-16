"""
School-focused onboarding for Apollo Agent.

Guides the user through setting up school-related skills and records
their preferences so the agent can adapt its behaviour accordingly.

Sections:
  1. User Profile — name, school, classes, goals
  2. Google Workspace — OAuth2 for Calendar, Drive, Gmail, etc.
  3. Canvas LMS — API token and base URL
  4. Todoist — task management API token
  5. Notion — notes & organization API key
  6. Additional preferences — study habits, alternative tools
  7. Summary & onboarding status written to config

The onboarding status dict is saved to config.yaml under the
``school_onboarding`` key so the agent's prompt builder can read it
at runtime and adapt (e.g. skip Todoist suggestions when it was
not set up, offer alternative task-saving methods, etc.).
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from apollo_cli.colors import Colors, color
from apollo_cli.config import (
    get_apollo_home,
    get_env_path,
    get_env_value,
    save_config,
    save_env_value,
    load_config,
)
from apollo_cli.setup import (
    print_header,
    print_info,
    print_success,
    print_warning,
    print_error,
    prompt,
    prompt_choice,
    prompt_yes_no,
    prompt_checklist,
)


# ─────────────────────────────────────────────────────────────────────
# Apollo-themed display helpers
# ─────────────────────────────────────────────────────────────────────

_SCHOOL_BANNER = r"""
[bold #FEE66E]┌──────────────────────────────────────────────────────────────┐[/]
[bold #FEE66E]│[/]  [bold #E88A5A]☀ Apollo School Setup[/]                                       [bold #FEE66E]│[/]
[bold #FEE66E]│[/]  [#FFF2CC]Get your school tools configured so Apollo can help you[/]     [bold #FEE66E]│[/]
[bold #FEE66E]│[/]  [#FFF2CC]with homework, scheduling, studying, and more.[/]              [bold #FEE66E]│[/]
[bold #FEE66E]└──────────────────────────────────────────────────────────────┘[/]
"""


def _print_apollo_banner():
    """Print the Apollo-themed school setup banner."""
    try:
        from rich.console import Console
        console = Console()
        console.print(_SCHOOL_BANNER)
    except ImportError:
        # Fallback to plain text
        print()
        print(color("┌──────────────────────────────────────────────────────────────┐", Colors.YELLOW))
        print(color("│  ☀ Apollo School Setup                                       │", Colors.YELLOW))
        print(color("│  Get your school tools configured so Apollo can help you      │", Colors.YELLOW))
        print(color("│  with homework, scheduling, studying, and more.              │", Colors.YELLOW))
        print(color("└──────────────────────────────────────────────────────────────┘", Colors.YELLOW))
        print()


def _print_section_banner(number: int, title: str, description: str):
    """Print a numbered section header in Apollo style."""
    print()
    print(color(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM))
    print(color(f"  ☀ Step {number}: {title}", Colors.CYAN, Colors.BOLD))
    print(color(f"  {description}", Colors.DIM))
    print(color(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM))
    print()


def _print_skip_note(service_name: str):
    """Print a skip note for a service."""
    print_info(f"  Skipped. You can set up {service_name} later with 'apollo setup school'.")


def _print_credentials_box(title: str, steps: List[str]):
    """Print a styled credentials instruction box."""
    print()
    print(color(f"  ┌─ {title} ─{'─' * max(0, 50 - len(title))}┐", Colors.CYAN))
    for i, step in enumerate(steps, 1):
        print(color(f"  │  {i}. {step}", Colors.DIM))
    print(color(f"  └{'─' * 56}┘", Colors.CYAN))
    print()


# ─────────────────────────────────────────────────────────────────────
# Section 1: User Profile & Preferences
# ─────────────────────────────────────────────────────────────────────

def _setup_user_profile(status: Dict[str, Any]) -> Dict[str, Any]:
    """Collect basic user info and school preferences."""
    _print_section_banner(1, "Your Profile", "Tell Apollo about yourself so it can help you better.")

    profile: Dict[str, Any] = status.get("user_profile", {})

    # Name
    current_name = profile.get("name", "")
    name = prompt("  What should Apollo call you?", current_name)
    if name:
        profile["name"] = name

    # School name
    current_school = profile.get("school", "")
    school = prompt("  What school do you attend?", current_school)
    if school:
        profile["school"] = school

    # Classes
    print()
    print_info("  List your current classes (comma-separated).")
    print_info("  Example: AP US History, Calculus BC, Spanish 3, CS 101")
    current_classes = ", ".join(profile.get("classes", []))
    classes_str = prompt("  Your classes", current_classes)
    if classes_str:
        profile["classes"] = [c.strip() for c in classes_str.split(",") if c.strip()]

    # Main goals
    print()
    print_info("  What are your main goals this semester? (comma-separated)")
    print_info("  Example: Raise GPA, finish college apps, learn Python")
    current_goals = ", ".join(profile.get("goals", []))
    goals_str = prompt("  Your goals", current_goals)
    if goals_str:
        profile["goals"] = [g.strip() for g in goals_str.split(",") if g.strip()]

    # Timezone / working hours
    print()
    current_tz = profile.get("timezone", "")
    tz = prompt("  Your timezone (e.g. America/New_York, America/Los_Angeles)", current_tz)
    if tz:
        profile["timezone"] = tz

    current_hours = profile.get("study_hours", "")
    hours = prompt("  Preferred study hours (e.g. 15:00-22:00)", current_hours or "15:00-22:00")
    if hours:
        profile["study_hours"] = hours

    if profile:
        print()
        print_success("Profile saved!")

    status["user_profile"] = profile
    return status


# ─────────────────────────────────────────────────────────────────────
# Section 2: Google Workspace (OAuth2)
# ─────────────────────────────────────────────────────────────────────

def _setup_google_auth(status: Dict[str, Any]) -> Dict[str, Any]:
    """Guide the user through Google OAuth2 setup."""
    _print_section_banner(
        2,
        "Google Workspace",
        "Connect Google Calendar, Drive, Gmail, and more.",
    )

    # Check if already set up
    google_token = get_apollo_home() / "google_token.json"
    already_authed = False
    if google_token.is_file():
        print_success("Google OAuth2 is already configured!")
        already_authed = True
        if not prompt_yes_no("  Reconfigure Google auth?", False):
            status["google_auth"] = {"configured": True, "skipped": False}
            return status

    print_info("  Google OAuth2 gives Apollo access to your Google Calendar, Drive,")
    print_info("  Gmail, Sheets, and Docs — all through a single login.")
    print()

    if not prompt_yes_no("  Set up Google Workspace now?", True):
        _print_skip_note("Google Workspace")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    # Step-by-step instructions
    _print_credentials_box("How to create Google OAuth credentials", [
        "Go to https://console.cloud.google.com/apis/credentials",
        "Create a project (or pick an existing one)",
        'Click "Enable APIs" — enable: Gmail, Calendar, Drive, Sheets, Docs, People',
        'Go to Credentials → Create Credentials → "OAuth 2.0 Client ID"',
        'Application type: "Desktop app" → Create',
        'Click "Download JSON" — save the file somewhere you can find it',
    ])

    print_info("  Once you have the JSON file, paste the full path below.")
    print_info("  Example: /home/you/Downloads/client_secret_12345.json")
    print()

    client_secret_path = prompt("  Path to client_secret JSON file")
    if not client_secret_path:
        print_warning("  No path provided — skipping Google setup.")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    client_secret_path = os.path.expanduser(client_secret_path.strip().strip("'\""))
    if not os.path.isfile(client_secret_path):
        print_error(f"  File not found: {client_secret_path}")
        print_info("  You can set up Google auth later with 'apollo setup school'.")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    # Run the setup script
    setup_script = get_apollo_home() / "skills" / "productivity" / "google-auth" / "scripts" / "setup.py"
    # Also check the project-level skills dir
    if not setup_script.is_file():
        setup_script = Path(__file__).parent.parent / "skills" / "productivity" / "google-auth" / "scripts" / "setup.py"

    if not setup_script.is_file():
        print_error("  Google auth setup script not found.")
        print_info("  Make sure the google-auth skill is installed.")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    import subprocess

    # Step 1: Copy client secret
    print()
    print_info("  Configuring client secret...")
    result = subprocess.run(
        [sys.executable, str(setup_script), "--client-secret", client_secret_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print_error(f"  Failed to configure client secret: {result.stderr.strip()}")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    print_success("  Client secret configured!")

    # Step 2: Get auth URL
    print()
    print_info("  Getting authorization URL...")
    result = subprocess.run(
        [sys.executable, str(setup_script), "--auth-url"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print_error(f"  Failed to get auth URL: {result.stderr.strip()}")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    auth_url = result.stdout.strip()
    print()
    print(color("  ┌─ Open this URL in your browser ─────────────────────────┐", Colors.CYAN))
    print(color(f"  │  {auth_url[:70]}", Colors.YELLOW))
    if len(auth_url) > 70:
        print(color(f"  │  {auth_url[70:140]}", Colors.YELLOW))
        if len(auth_url) > 140:
            print(color(f"  │  {auth_url[140:]}", Colors.YELLOW))
    print(color("  └──────────────────────────────────────────────────────────┘", Colors.CYAN))
    print()
    print_info("  Sign in with your Google account and authorize access.")
    print_info("  After authorizing, you'll be redirected to a page (it may show an error).")
    print_info("  Copy the ENTIRE URL from your browser's address bar and paste it below.")
    print()

    auth_response = prompt("  Paste the redirect URL or authorization code here")
    if not auth_response:
        print_warning("  No code provided — skipping.")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    # Step 3: Exchange the code
    result = subprocess.run(
        [sys.executable, str(setup_script), "--auth-code", auth_response.strip()],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print_error(f"  Authorization failed: {result.stderr.strip()}")
        status["google_auth"] = {"configured": already_authed, "skipped": True}
        return status

    # Step 4: Verify
    result = subprocess.run(
        [sys.executable, str(setup_script), "--check"],
        capture_output=True, text=True,
    )
    if "AUTHENTICATED" in result.stdout:
        print()
        print_success("  Google Workspace connected! Calendar, Drive, Gmail, and more are ready.")
        status["google_auth"] = {"configured": True, "skipped": False}
    else:
        print_warning("  Could not verify authentication. You may need to redo this step.")
        status["google_auth"] = {"configured": False, "skipped": False}

    # Ask about school Google account password for browser SSO
    print()
    print_info("  Some school accounts use browser-based SSO for Google Drive access.")
    print_info("  If your school uses Microsoft SSO or a custom login page, Apollo can")
    print_info("  save your credentials to log in automatically via the browser.")
    print()
    if prompt_yes_no("  Save your school Google account email/password for browser SSO?", False):
        email = prompt("  School email address")
        password = prompt("  School account password", password=True)
        if email:
            status.setdefault("user_profile", {})["school_email"] = email
        if password:
            # Save to .env for secure storage (0600 permissions)
            save_env_value("SCHOOL_GOOGLE_PASSWORD", password)
            print_success("  Credentials saved securely to ~/.apollo/.env")
            print_info("  Apollo will use these for browser-based Google Drive access.")
    else:
        print_info("  No problem — Apollo will ask when needed.")

    return status


# ─────────────────────────────────────────────────────────────────────
# Section 3: Canvas LMS
# ─────────────────────────────────────────────────────────────────────

def _setup_canvas(status: Dict[str, Any]) -> Dict[str, Any]:
    """Guide the user through Canvas LMS API setup."""
    _print_section_banner(
        3,
        "Canvas LMS",
        "Connect to your school's Canvas for assignments, grades, and submissions.",
    )

    existing_token = get_env_value("CANVAS_API_TOKEN")
    existing_url = get_env_value("CANVAS_BASE_URL")

    if existing_token and existing_url:
        print_success(f"  Canvas is already configured!")
        print_info(f"  Instance: {existing_url}")
        if not prompt_yes_no("  Reconfigure Canvas?", False):
            status["canvas"] = {"configured": True, "skipped": False}
            return status

    print_info("  Canvas is the learning management system used by many schools.")
    print_info("  Connecting it lets Apollo see your courses, assignments, and due dates.")
    print()

    if not prompt_yes_no("  Set up Canvas LMS now?", True):
        _print_skip_note("Canvas LMS")
        status["canvas"] = {"configured": bool(existing_token and existing_url), "skipped": True}
        return status

    _print_credentials_box("How to get your Canvas API token", [
        "Log in to Canvas in your browser",
        "Click your profile icon → Settings",
        'Scroll to "Approved Integrations"',
        'Click "+ New Access Token"',
        'Name it "Apollo Agent", set optional expiry, click "Generate Token"',
        "Copy the token (you won't be able to see it again!)",
    ])

    # Canvas base URL
    print_info("  Your Canvas URL is what you see in the browser when you log in.")
    print_info("  Example: https://yourschool.instructure.com")
    print()

    base_url = prompt("  Canvas URL (e.g. https://yourschool.instructure.com)", existing_url or "")
    if base_url:
        # Strip trailing slash
        base_url = base_url.rstrip("/")
        save_env_value("CANVAS_BASE_URL", base_url)

    print()
    api_token = prompt("  Canvas API token", password=True)
    if api_token:
        save_env_value("CANVAS_API_TOKEN", api_token)

    if base_url and api_token:
        print()
        print_success("  Canvas LMS connected!")
        print_info("  Apollo can now list your courses, check assignments, and track due dates.")
        status["canvas"] = {"configured": True, "skipped": False}
    else:
        if base_url or api_token:
            print_warning("  Partial setup — both the URL and API token are required.")
        else:
            print_info("  Skipped Canvas setup.")
        status["canvas"] = {"configured": False, "skipped": not (base_url or api_token)}

    return status


# ─────────────────────────────────────────────────────────────────────
# Section 4: Todoist
# ─────────────────────────────────────────────────────────────────────

def _setup_todoist(status: Dict[str, Any]) -> Dict[str, Any]:
    """Guide the user through Todoist API setup."""
    _print_section_banner(
        4,
        "Todoist — Task Management",
        "Connect Todoist so Apollo can create, schedule, and track your tasks.",
    )

    existing_token = get_env_value("TODOIST_API_TOKEN")

    if existing_token:
        print_success("  Todoist is already configured!")
        if not prompt_yes_no("  Reconfigure Todoist?", False):
            status["todoist"] = {"configured": True, "skipped": False}
            return status

    print_info("  Todoist lets Apollo create tasks with smart scheduling,")
    print_info("  duration estimates, and priority based on your calendar.")
    print()

    if not prompt_yes_no("  Set up Todoist now?", True):
        _print_skip_note("Todoist")
        status["todoist"] = {"configured": bool(existing_token), "skipped": True}

        # Ask about alternative task management
        print()
        print_info("  Since you're skipping Todoist, Apollo needs to know how you")
        print_info("  want tasks and reminders handled.")
        alt_choices = [
            "Just tell me — I'll manage tasks myself",
            "Save tasks to a text file (~/.apollo/tasks.txt)",
            "Use Notion (set up in next step)",
            "I'll set up Todoist later",
        ]
        alt_idx = prompt_choice("  How should Apollo handle tasks?", alt_choices, 0)
        alt_map = {0: "verbal", 1: "text_file", 2: "notion", 3: "todoist_later"}
        status["todoist"]["alternative"] = alt_map.get(alt_idx, "verbal")

        return status

    _print_credentials_box("How to get your Todoist API token", [
        "Open https://app.todoist.com",
        "Go to Settings → Integrations → Developer",
        "Copy your API token",
    ])

    api_token = prompt("  Todoist API token", password=True)
    if api_token:
        save_env_value("TODOIST_API_TOKEN", api_token)
        print()
        print_success("  Todoist connected!")
        print_info("  Apollo will create tasks with smart scheduling and duration estimates.")
        status["todoist"] = {"configured": True, "skipped": False}
    else:
        print_info("  Skipped Todoist setup.")
        status["todoist"] = {"configured": False, "skipped": True, "alternative": "todoist_later"}

    return status


# ─────────────────────────────────────────────────────────────────────
# Section 5: Notion
# ─────────────────────────────────────────────────────────────────────

def _setup_notion(status: Dict[str, Any]) -> Dict[str, Any]:
    """Guide the user through Notion API setup."""
    _print_section_banner(
        5,
        "Notion — Notes & Organization",
        "Connect Notion for notes, wikis, and project databases.",
    )

    existing_key = get_env_value("NOTION_API_KEY")

    if existing_key:
        print_success("  Notion is already configured!")
        if not prompt_yes_no("  Reconfigure Notion?", False):
            status["notion"] = {"configured": True, "skipped": False}
            return status

    print_info("  Notion lets Apollo search your notes, create pages, and")
    print_info("  query databases — great for organizing class notes and projects.")
    print()

    if not prompt_yes_no("  Set up Notion now?", False):
        _print_skip_note("Notion")
        status["notion"] = {"configured": bool(existing_key), "skipped": True}
        return status

    _print_credentials_box("How to get your Notion API key", [
        "Go to https://notion.so/my-integrations",
        'Click "+ New integration"',
        "Name it (e.g. Apollo Agent), select your workspace",
        "Copy the API key (starts with ntn_ or secret_)",
        "IMPORTANT: Share your pages/databases with the integration in Notion",
        '  (Click "..." on a page → "Connect to" → your integration)',
    ])

    api_key = prompt("  Notion API key", password=True)
    if api_key:
        save_env_value("NOTION_API_KEY", api_key)
        print()
        print_success("  Notion connected!")
        status["notion"] = {"configured": True, "skipped": False}
    else:
        print_info("  Skipped Notion setup.")
        status["notion"] = {"configured": False, "skipped": True}

    return status


# ─────────────────────────────────────────────────────────────────────
# Section 6: Additional Preferences
# ─────────────────────────────────────────────────────────────────────

def _setup_additional_preferences(status: Dict[str, Any]) -> Dict[str, Any]:
    """Collect additional school-related preferences."""
    _print_section_banner(
        6,
        "Preferences & Study Habits",
        "Help Apollo understand how you work best.",
    )

    prefs: Dict[str, Any] = status.get("preferences", {})

    # Note-taking preference
    print_info("  Where do you primarily take notes?")
    note_choices = [
        "Google Docs",
        "Notion",
        "Obsidian",
        "Apple Notes / Other app",
        "Paper / I don't take digital notes",
    ]
    current_note = prefs.get("note_taking", "")
    note_map = {0: "google_docs", 1: "notion", 2: "obsidian", 3: "other_app", 4: "paper"}
    default_note = next((i for i, v in note_map.items() if v == current_note), 0)
    note_idx = prompt_choice("  Primary note-taking method:", note_choices, default_note)
    prefs["note_taking"] = note_map.get(note_idx, "google_docs")

    # Study style
    print()
    print_info("  How do you prefer to study?")
    study_choices = [
        "Flashcards (Quizlet, Anki)",
        "Practice problems / quizzes",
        "Reading and summarizing",
        "Mix of everything",
    ]
    study_map = {0: "flashcards", 1: "practice", 2: "reading", 3: "mixed"}
    current_study = prefs.get("study_style", "")
    default_study = next((i for i, v in study_map.items() if v == current_study), 3)
    study_idx = prompt_choice("  Preferred study method:", study_choices, default_study)
    prefs["study_style"] = study_map.get(study_idx, "mixed")

    # Assignment workflow
    print()
    print_info("  When Apollo helps with assignments, what should it prioritize?")
    workflow_choices = [
        "Understanding — explain concepts, don't just give answers",
        "Efficiency — help me get things done quickly",
        "Balance — explain when I'm stuck, efficient otherwise",
    ]
    workflow_map = {0: "understanding", 1: "efficiency", 2: "balance"}
    current_workflow = prefs.get("assignment_approach", "")
    default_workflow = next((i for i, v in workflow_map.items() if v == current_workflow), 2)
    workflow_idx = prompt_choice("  Assignment approach:", workflow_choices, default_workflow)
    prefs["assignment_approach"] = workflow_map.get(workflow_idx, "balance")

    # Any additional info
    print()
    print_info("  Anything else Apollo should know? (e.g. learning differences,")
    print_info("  preferred communication style, upcoming exams, etc.)")
    current_notes = prefs.get("additional_notes", "")
    additional = prompt("  Additional notes (or press Enter to skip)", current_notes)
    if additional:
        prefs["additional_notes"] = additional

    status["preferences"] = prefs
    print()
    print_success("  Preferences saved!")

    return status


# ─────────────────────────────────────────────────────────────────────
# Summary & status report
# ─────────────────────────────────────────────────────────────────────

def _print_onboarding_summary(status: Dict[str, Any]):
    """Print a final summary of what was configured."""
    print()
    print(color("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM))
    print(color("  ☀ School Setup Complete!", Colors.CYAN, Colors.BOLD))
    print(color("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM))
    print()

    # Profile summary
    profile = status.get("user_profile", {})
    if profile.get("name"):
        print(f"   {color('User:', Colors.YELLOW)}     {profile['name']}")
    if profile.get("school"):
        print(f"   {color('School:', Colors.YELLOW)}   {profile['school']}")
    if profile.get("classes"):
        print(f"   {color('Classes:', Colors.YELLOW)}  {', '.join(profile['classes'])}")
    if profile.get("goals"):
        print(f"   {color('Goals:', Colors.YELLOW)}    {', '.join(profile['goals'])}")
    print()

    # Service status
    services = [
        ("Google Workspace", "google_auth"),
        ("Canvas LMS", "canvas"),
        ("Todoist", "todoist"),
        ("Notion", "notion"),
    ]

    configured_count = 0
    skipped_services = []

    for label, key in services:
        svc = status.get(key, {})
        if svc.get("configured"):
            print(f"   {color('✓', Colors.GREEN)} {label}")
            configured_count += 1
        elif svc.get("skipped"):
            print(f"   {color('–', Colors.DIM)} {label} {color('(skipped)', Colors.DIM)}")
            skipped_services.append(label)
        else:
            print(f"   {color('✗', Colors.RED)} {label} {color('(not configured)', Colors.DIM)}")
            skipped_services.append(label)

    print()

    # Adaptation notes
    todoist_status = status.get("todoist", {})
    if not todoist_status.get("configured"):
        alt = todoist_status.get("alternative", "verbal")
        alt_labels = {
            "verbal": "Apollo will mention tasks verbally — you manage them yourself",
            "text_file": "Apollo will save tasks to ~/.apollo/tasks.txt",
            "notion": "Apollo will try to save tasks to Notion",
            "todoist_later": "Apollo will remind you to set up Todoist",
        }
        print_info(f"  Task management: {alt_labels.get(alt, 'verbal')}")

    if not status.get("google_auth", {}).get("configured"):
        print_info("  Google services: Apollo will ask you to set up when needed")

    if not status.get("canvas", {}).get("configured"):
        print_info("  Canvas: Apollo won't be able to check assignments automatically")

    print()
    print(f"   {color(f'{configured_count}/{len(services)}', Colors.GREEN)} services configured")

    if skipped_services:
        print()
        print_info(f"  To set up skipped services later: {color('apollo setup school', Colors.GREEN)}")

    print()
    print(color("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM))
    print()
    print_info("  Apollo will adapt to your setup — if a service isn't configured,")
    print_info("  it'll suggest alternatives or ask how you'd like to handle things.")
    print()
    print(color("  ☀ You're all set! Start chatting with: apollo", Colors.CYAN, Colors.BOLD))
    print()


# ─────────────────────────────────────────────────────────────────────
# Save status to USER.md memory for agent access
# ─────────────────────────────────────────────────────────────────────

def _save_to_user_memory(status: Dict[str, Any]):
    """Save key onboarding info to USER.md so the agent can read it at runtime."""
    home = get_apollo_home()
    memories_dir = home / "memories"
    memories_dir.mkdir(parents=True, exist_ok=True)
    user_md = memories_dir / "USER.md"

    # Build the onboarding section
    lines = []
    lines.append("## School Onboarding")
    lines.append("")

    profile = status.get("user_profile", {})
    if profile.get("name"):
        lines.append(f"- Name: {profile['name']}")
    if profile.get("school"):
        lines.append(f"- School: {profile['school']}")
    if profile.get("school_email"):
        lines.append(f"- School email: {profile['school_email']}")
    if profile.get("classes"):
        lines.append(f"- Classes: {', '.join(profile['classes'])}")
    if profile.get("goals"):
        lines.append(f"- Goals: {', '.join(profile['goals'])}")
    if profile.get("timezone"):
        lines.append(f"- Timezone: {profile['timezone']}")
    if profile.get("study_hours"):
        lines.append(f"- Study hours: {profile['study_hours']}")

    lines.append("")
    lines.append("### Configured Services")
    for key in ("google_auth", "canvas", "todoist", "notion"):
        svc = status.get(key, {})
        configured = svc.get("configured", False)
        lines.append(f"- {key}: {'configured' if configured else 'not configured'}")
        if key == "todoist" and not configured:
            alt = svc.get("alternative", "verbal")
            lines.append(f"  - Alternative task method: {alt}")

    prefs = status.get("preferences", {})
    if prefs:
        lines.append("")
        lines.append("### Preferences")
        if prefs.get("note_taking"):
            lines.append(f"- Note-taking: {prefs['note_taking']}")
        if prefs.get("study_style"):
            lines.append(f"- Study style: {prefs['study_style']}")
        if prefs.get("assignment_approach"):
            lines.append(f"- Assignment approach: {prefs['assignment_approach']}")
        if prefs.get("additional_notes"):
            lines.append(f"- Notes: {prefs['additional_notes']}")

    onboarding_block = "\n".join(lines)

    # Read existing USER.md and replace or append the onboarding section
    existing_content = ""
    if user_md.is_file():
        existing_content = user_md.read_text(encoding="utf-8")

    marker_start = "## School Onboarding"
    marker_end_candidates = ["## ", "---"]

    if marker_start in existing_content:
        # Replace existing section
        start_idx = existing_content.index(marker_start)
        # Find the next section heading or end of file
        end_idx = len(existing_content)
        rest = existing_content[start_idx + len(marker_start):]
        for marker in marker_end_candidates:
            pos = rest.find(marker)
            if pos > 0:
                end_idx = min(end_idx, start_idx + len(marker_start) + pos)

        new_content = existing_content[:start_idx] + onboarding_block + "\n\n" + existing_content[end_idx:]
    else:
        # Append
        separator = "\n\n" if existing_content and not existing_content.endswith("\n\n") else ""
        if existing_content and not existing_content.endswith("\n"):
            separator = "\n\n"
        new_content = existing_content + separator + onboarding_block + "\n"

    user_md.write_text(new_content, encoding="utf-8")
    from apollo_cli.config import _secure_file
    _secure_file(user_md)


# ─────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────

def setup_school(config: Dict[str, Any]):
    """Run the school-focused onboarding wizard.

    This is both a standalone wizard (``apollo setup school``) and a
    section that can be called from the main setup wizard.
    """
    _print_apollo_banner()

    # Load existing status if any
    status: Dict[str, Any] = config.get("school_onboarding", {})
    status.setdefault("completed", False)

    print_info("  This will walk you through setting up school-related tools.")
    print_info("  You can skip any step and come back later with 'apollo setup school'.")
    print_info("  Press Ctrl+C at any time to exit (progress is saved).")
    print()

    try:
        # Step 1: User Profile
        status = _setup_user_profile(status)
        config["school_onboarding"] = status
        save_config(config)

        # Step 2: Google Workspace
        status = _setup_google_auth(status)
        config["school_onboarding"] = status
        save_config(config)

        # Step 3: Canvas LMS
        status = _setup_canvas(status)
        config["school_onboarding"] = status
        save_config(config)

        # Step 4: Todoist
        status = _setup_todoist(status)
        config["school_onboarding"] = status
        save_config(config)

        # Step 5: Notion
        status = _setup_notion(status)
        config["school_onboarding"] = status
        save_config(config)

        # Step 6: Preferences
        status = _setup_additional_preferences(status)
        config["school_onboarding"] = status

        # Mark as completed
        status["completed"] = True
        config["school_onboarding"] = status
        save_config(config)

        # Save to USER.md for agent access
        _save_to_user_memory(status)

        # Print summary
        _print_onboarding_summary(status)

    except (KeyboardInterrupt, EOFError):
        # Save whatever we have so far
        config["school_onboarding"] = status
        save_config(config)
        _save_to_user_memory(status)
        print()
        print_info("  Progress saved! Run 'apollo setup school' to continue later.")
        print()
