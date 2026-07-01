import json
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
TOPIC = os.getenv("NTFY_TOPIC")
OWNER = os.getenv("OWNER")
REPO = os.getenv("REPO")
INTERVAL = int(os.getenv("CHECK_INTERVAL", "20"))
if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN not found in .env")
API = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
}


def load_seen():
    if not os.path.exists("seen.json"):
        return set()

    try:
        with open("seen.json", "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    with open("seen.json", "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)


def notify(issue):
    print("Sending ntfy notification...")
    number = issue["number"]
    title = issue["title"]
    url = issue["html_url"]

    author = issue["user"]["login"]
    created = issue["created_at"]

    labels = [label["name"] for label in issue["labels"]]
    label_text = ", ".join(labels) if labels else "None"

    body = f"""
Issue #{number}

{title}

Author : {author}
Labels : {label_text}
Created: {created}

{url}
"""

    response = requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=body.encode("utf-8"),
        headers={
            "Title": f"New Cognee Issue #{number}",
            "Click": url,
            "Priority": "urgent",
            "Tags": "rocket,github",
            "Markdown": "yes",
        },
        timeout=10,
    )

    response.raise_for_status()
    

def current_time():
    return datetime.now().strftime("%H:%M:%S")


seen = load_seen()
print(f"Loaded {len(seen)} seen issues")
# ----------------------------
# First Run
# ----------------------------
if not seen:
    print("📦 First run detected.")
    print("Recording existing issues...")

    response = requests.get(
        API,
        headers=HEADERS,
        params={
            "state": "open",
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
        },
        timeout=15,
    )

    response.raise_for_status()

    for issue in response.json():
        if "pull_request" not in issue:
            seen.add(issue["number"])
            print(f"Saved issue #{issue['number']} to seen.json")

    save_seen(seen)

    print(f"✅ Recorded {len(seen)} existing issues.")
    print("Waiting for NEW issues...\n")

print("=" * 60)
print("🚀 Cognee Issue Notifier Started")
print(f"📂 Repository : {OWNER}/{REPO}")
print(f"⏱️  Interval   : {INTERVAL} seconds")
print("=" * 60)

while True:

    try:

        response = requests.get(
            API,
            headers=HEADERS,
            params={
                "state": "open",
                "sort": "created",
                "direction": "desc",
                "per_page": 100,
            },
            timeout=15,
        )

        response.raise_for_status()

        issues = response.json()

        new_count = 0

        for issue in reversed(issues):

            if "pull_request" in issue:
                continue

            issue_id = issue["number"]
            print(f"Checking issue #{issue['number']} (ID: {issue_id})")

            if issue_id in seen:
                continue

            seen.add(issue_id)
            save_seen(seen)

            try:
                notify(issue)
            except Exception as e:
                print(f"Notification failed: {e}")

            labels = [l["name"] for l in issue["labels"]]
            label_text = ", ".join(labels) if labels else "None"

            print()
            print("=" * 70)
            print(f"🚀 NEW ISSUE #{issue['number']}")
            print("-" * 70)
            print(f"Title   : {issue['title']}")
            print(f"Author  : {issue['user']['login']}")
            print(f"Labels  : {label_text}")
            print(f"Created : {issue['created_at']}")
            print(f"URL     : {issue['html_url']}")
            print("=" * 70)
            print()

            new_count += 1

        if new_count == 0:
            print(f"[{current_time()}] ✓ Checked - No new issues")

    except requests.exceptions.RequestException as e:
        print(f"[{current_time()}] ❌ Network Error")
        print(e)

    except Exception as e:
        print(f"[{current_time()}] ❌ Unexpected Error")
        print(e)

    time.sleep(INTERVAL)