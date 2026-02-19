"""BotEmail Tool for CrewAI - provides AI agents with free, disposable email inboxes."""

from typing import Any, Literal, Optional, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class BotEmailToolSchema(BaseModel):
    """Input schema for BotEmailTool."""

    action: Literal["create_inbox", "get_emails", "delete_email"] = Field(
        ...,
        description=(
            "Action to perform: "
            "'create_inbox' to create a new email inbox (returns email address and API key), "
            "'get_emails' to retrieve emails from an inbox (requires email and api_key), "
            "'delete_email' to delete a specific email (requires email, api_key, and email_id)."
        ),
    )
    email: Optional[str] = Field(
        default=None,
        description="The email address of the inbox. Required for 'get_emails' and 'delete_email' actions.",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="The API key for the inbox. Required for 'get_emails' and 'delete_email' actions.",
    )
    email_id: Optional[str] = Field(
        default=None,
        description="The ID of the email to delete. Required for the 'delete_email' action.",
    )


class BotEmailTool(BaseTool):
    """
    BotEmailTool - Provides AI agents with free, disposable email inboxes via botemail.ai.

    This tool allows AI agents to:
    - Create a new email inbox (no sign-up required)
    - Read emails received in that inbox
    - Delete specific emails

    Useful for agents that need to receive emails, verify registrations, or test
    email-based workflows without requiring a real email account.

    API base: https://api.botemail.ai
    """

    name: str = "BotEmail Agent Inbox"
    description: str = (
        "A tool that gives AI agents access to free, disposable email inboxes via botemail.ai. "
        "Use 'create_inbox' to get a new email address and API key, "
        "'get_emails' to read received emails, "
        "or 'delete_email' to remove a specific email from the inbox."
    )
    args_schema: Type[BaseModel] = BotEmailToolSchema
    base_url: str = "https://api.botemail.ai"

    def _run(self, **kwargs: Any) -> Any:
        action = kwargs.get("action")

        if action == "create_inbox":
            return self._create_inbox()
        elif action == "get_emails":
            email = kwargs.get("email")
            api_key = kwargs.get("api_key")
            if not email or not api_key:
                return "Error: 'email' and 'api_key' are required for the 'get_emails' action."
            return self._get_emails(email, api_key)
        elif action == "delete_email":
            email = kwargs.get("email")
            api_key = kwargs.get("api_key")
            email_id = kwargs.get("email_id")
            if not email or not api_key or not email_id:
                return "Error: 'email', 'api_key', and 'email_id' are required for the 'delete_email' action."
            return self._delete_email(email, api_key, email_id)
        else:
            return f"Error: Unknown action '{action}'. Valid actions are: create_inbox, get_emails, delete_email."

    def _create_inbox(self) -> str:
        """Create a new email inbox and return the email address and API key."""
        try:
            response = requests.post(f"{self.base_url}/api/create-account", timeout=15)
            response.raise_for_status()
            data = response.json()
            email = data.get("email", "")
            api_key = data.get("apiKey", "")
            return (
                f"Inbox created successfully.\n"
                f"Email: {email}\n"
                f"API Key: {api_key}\n"
                f"Use these credentials with 'get_emails' to check for incoming messages."
            )
        except requests.RequestException as e:
            return f"Error creating inbox: {str(e)}"

    def _get_emails(self, email: str, api_key: str) -> str:
        """Retrieve emails from the specified inbox."""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                f"{self.base_url}/api/emails/{email}",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            emails = response.json()

            if not emails:
                return f"No emails found in inbox: {email}"

            result_lines = [f"Found {len(emails)} email(s) in {email}:\n"]
            for i, msg in enumerate(emails, 1):
                result_lines.append(f"--- Email {i} ---")
                result_lines.append(f"ID:      {msg.get('id', 'N/A')}")
                result_lines.append(f"From:    {msg.get('from', 'N/A')}")
                result_lines.append(f"Subject: {msg.get('subject', '(no subject)')}")
                result_lines.append(f"Date:    {msg.get('date', 'N/A')}")
                body = msg.get("body") or msg.get("text") or msg.get("html") or ""
                if body:
                    # Truncate very long bodies
                    preview = body[:500] + ("..." if len(body) > 500 else "")
                    result_lines.append(f"Body:\n{preview}")
                result_lines.append("")

            return "\n".join(result_lines)
        except requests.RequestException as e:
            return f"Error retrieving emails: {str(e)}"

    def _delete_email(self, email: str, api_key: str, email_id: str) -> str:
        """Delete a specific email from the inbox."""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.delete(
                f"{self.base_url}/api/emails/{email}/{email_id}",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            return f"Email '{email_id}' deleted successfully from inbox: {email}"
        except requests.RequestException as e:
            return f"Error deleting email: {str(e)}"
