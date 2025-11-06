# gmail_tool.py
import os
from typing import List, Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Start read-only; add 'gmail.modify' if you need to mark as read.
SCOPES = os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly").split(",")

def _gmail_service() -> Any:
    """
    Returns an authenticated Gmail service client using credentials.json/token.json.
    Looks for CREDENTIALS_PATH and TOKEN_PATH env vars, falls back to local files.
    """
    creds: Optional[Credentials] = None
    credentials_path = os.getenv("CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("TOKEN_PATH", "token.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # Opens a local browser once during first run
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ---------- TOOLS (plain functions) ----------

def gmail_list_unread(q: str = "is:unread", max_results: int = 25) -> List[Dict[str, Any]]:
    """
    List unread messages with light metadata.
    Use Gmail search syntax in `q` (e.g., 'is:unread newer_than:7d -category:promotions').
    Returns: [{id, threadId, from, subject, date, snippet}]
    """
    service = _gmail_service()
    resp = service.users().messages().list(userId="me", q=q, maxResults=max_results).execute()
    ids = resp.get("messages", [])
    results: List[Dict[str, Any]] = []

    for m in ids:
        full = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
        results.append({
            "id": m["id"],
            "threadId": m.get("threadId"),
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "snippet": full.get("snippet"),
        })

    return results

def gmail_get_message(id: str, format: str = "full") -> Dict[str, Any]:
    """
    Get a single message by ID.
    format: 'full' | 'metadata' | 'raw' | 'minimal'
    Returns the Gmail Message resource.
    """
    service = _gmail_service()
    return service.users().messages().get(userId="me", id=id, format=format).execute()

def gmail_search(q: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    General Gmail search using Gmail search operators
    (e.g., 'from:foo is:unread has:attachment newer_than:30d').
    Returns: [{id, threadId}]
    """
    service = _gmail_service()
    resp = service.users().messages().list(userId="me", q=q, maxResults=max_results).execute()
    return resp.get("messages", [])

def gmail_mark_read(id: str) -> Dict[str, Any]:
    """
    Mark a message as READ by removing the UNREAD label.
    Requires 'https://www.googleapis.com/auth/gmail.modify' scope in SCOPES.
    """
    if "https://www.googleapis.com/auth/gmail.modify" not in [s.strip() for s in SCOPES]:
        return {"error": "Server not configured with gmail.modify scope. Set GMAIL_SCOPES env and re-auth."}

    service = _gmail_service()
    body = {"removeLabelIds": ["UNREAD"], "addLabelIds": []}
    return service.users().messages().modify(userId="me", id=id, body=body).execute()

if __name__ == "__main__":
    # minimal self-test; only runs if you execute `python tool.py`
    unread_emails = gmail_list_unread(max_results=5)
    print("Unread Emails:", unread_emails)
    unread = gmail_list_unread(q="is:unread newer_than:7d -category:promotions", max_results=10)
    for m in unread:
        print(m["id"], m["from"], m["subject"], m["date"])

# B) Get a full message (payload, headers, parts)
    if unread:
        msg = gmail_get_message(id=unread[0]["id"], format="full")
        print("snippet:", msg.get("snippet"))

# C) Search for anything (returns IDs)
    ids = gmail_search(q='from:github.com has:attachment newer_than:30d', max_results=20)
    print("found", len(ids), "messages")

# D) Mark a message as read
    if unread:
        result = gmail_mark_read(id=unread[0]["id"])
        print("mark_read -> labelIds:", result.get("labelIds"))
