"""
Slack and Microsoft Teams webhook notification delivery.
Both support free incoming webhooks — no auth tokens needed, just the webhook URL.
"""
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {
    "Critical": "🔴",
    "High": "🟠",
    "Medium": "🟡",
    "Low": "🟢",
}

class SlackNotifier:
    """Sends Propex security alerts to a Slack channel via incoming webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_alert(self, cve_id: str, package_name: str, repo_url: str,
                          propex_score: float, severity: str, issue_url: Optional[str] = None) -> bool:
        """Send a rich Slack Block Kit message for a security finding."""
        emoji = SEVERITY_EMOJI.get(severity, "⚪")
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {severity} Security Alert — {cve_id}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Package:*\n`{package_name}`"},
                    {"type": "mrkdwn", "text": f"*Propex Score:*\n`{propex_score}/10`"},
                    {"type": "mrkdwn", "text": f"*Repository:*\n<{repo_url}|{repo_url.split('/')[-1]}>"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"}
                ]
            }
        ]
        
        if issue_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View GitHub Issue"},
                        "url": issue_url,
                        "style": "danger" if severity in ("Critical", "High") else "primary"
                    }
                ]
            })
        
        payload = {"blocks": blocks, "text": f"[{severity}] {cve_id} detected in {package_name}"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(self.webhook_url, json=payload)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Slack notification failed: {e}")
        return False


class TeamsNotifier:
    """Sends Propex security alerts to a Microsoft Teams channel via incoming webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_alert(self, cve_id: str, package_name: str, repo_url: str,
                          propex_score: float, severity: str, issue_url: Optional[str] = None) -> bool:
        """Send an Adaptive Card to a Teams channel."""
        emoji = SEVERITY_EMOJI.get(severity, "⚪")
        
        # Teams uses Adaptive Cards format
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": f"{emoji} {severity} — {cve_id}"
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Package", "value": package_name},
                                    {"title": "Repository", "value": repo_url.split("/")[-1]},
                                    {"title": "Propex Score", "value": f"{propex_score}/10"},
                                    {"title": "Severity", "value": severity}
                                ]
                            }
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "View Repository",
                                "url": repo_url
                            },
                            *([{
                                "type": "Action.OpenUrl",
                                "title": "View GitHub Issue",
                                "url": issue_url
                            }] if issue_url else [])
                        ]
                    }
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(self.webhook_url, json=payload)
                return resp.status_code in (200, 202)
            except Exception as e:
                logger.error(f"Teams notification failed: {e}")
        return False
