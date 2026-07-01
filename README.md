# Issues Notifier

A small Python script that watches a GitHub repository for new issues and sends notifications to an ntfy topic.

## Features
- Checks GitHub issues on a set interval
- Avoids duplicate notifications by tracking seen issues in `seen.json`
- Sends alerts to ntfy with issue details

## Setup
1. Install dependencies:
   `pip install -r requirements.txt`
2. Create a `.env` file with:
   - `GITHUB_TOKEN`
   - `NTFY_TOPIC`
   - `OWNER`
   - `REPO`
   - `CHECK_INTERVAL` (optional)
3. Run the script:
   `python notifier.py`

## Notes
The script stores previously seen issue numbers in `seen.json` so it only notifies you about new issues.
