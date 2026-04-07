"""
MCP Tooling: Real Gmail parser for reward points, cashback alerts, and subscription emails.
Uses Google Gmail API v1 with OAuth2. Falls back to demo data if credentials not available.
"""
import os
import base64
import json
import re
from typing import List, Dict, Any, Optional
from email import message_from_bytes

# Google API imports - graceful degradation if not installed
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("WARNING: google-api-python-client not installed. Gmail features disabled.")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "../../gmail_token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "../../gmail_credentials.json")

# Search query covering reward, points, cashback, subscriptions
GMAIL_QUERY = (
    'subject:("reward" OR "points" OR "cashback" OR "expiring" OR "subscription" OR "renewal" '
    'OR "credit card offer" OR "statement" OR "miles")'
)


class GmailRewardParser:
    def __init__(self):
        self.service = None
        self._connect()

    def _connect(self):
        """Initializes Gmail API service using stored OAuth2 token."""
        if not GMAIL_AVAILABLE:
            return

        creds: Optional[Credentials] = None
        token_path = os.path.abspath(TOKEN_FILE)
        creds_path = os.path.abspath(CREDENTIALS_FILE)

        # Load existing token
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)
            except Exception as e:
                print(f"Token load failed: {e}")

        # Refresh or run OAuth flow
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None

        if not creds or not creds.valid:
            if os.path.exists(creds_path):
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            else:
                print(f"No Gmail credentials found at {creds_path}. Gmail disabled.")
                return

        try:
            self.service = build("gmail", "v1", credentials=creds)
            print("✅ Gmail API connected.")
        except Exception as e:
            print(f"Gmail service build failed: {e}")

    def _decode_body(self, payload: dict) -> str:
        """Recursively decodes email body from MIME parts."""
        body = ""
        if payload.get("body", {}).get("data"):
            raw = payload["body"]["data"]
            body = base64.urlsafe_b64decode(raw + "==").decode("utf-8", errors="ignore")
        elif payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") in ("text/plain", "text/html"):
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body += base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
        return body

    async def fetch_emails(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """Fetches real emails from Gmail matching the reward/subscription query."""
        if not self.service:
            return self._demo_emails()

        try:
            results = self.service.users().messages().list(
                userId="me", q=GMAIL_QUERY, maxResults=max_results
            ).execute()
            messages = results.get("messages", [])
            emails = []
            for msg in messages:
                detail = self.service.users().messages().get(
                    userId="me", messageId=msg["id"], format="full"
                ).execute()
                subject = next(
                    (h["value"] for h in detail["payload"].get("headers", []) if h["name"] == "Subject"),
                    "(No Subject)"
                )
                sender = next(
                    (h["value"] for h in detail["payload"].get("headers", []) if h["name"] == "From"),
                    "Unknown"
                )
                body = self._decode_body(detail["payload"])
                emails.append({
                    "id": msg["id"],
                    "subject": subject,
                    "from": sender,
                    "snippet": detail.get("snippet", ""),
                    "body": body[:2000]  # Limit to avoid token overflow
                })
            return emails
        except Exception as e:
            print(f"Gmail fetch error: {e}")
            return self._demo_emails()

    def _demo_emails(self) -> List[Dict[str, Any]]:
        """Returns realistic demo email data when Gmail is not configured."""
        return [
            {
                "id": "demo_1",
                "subject": "Your Chase Sapphire: 50,000 Points Expiring Oct 31st",
                "from": "noreply@chase.com",
                "snippet": "Don't let your points expire. Redeem 50,000 Chase Ultimate Rewards points before Oct 31.",
                "body": "Hello Valued Customer, Your Chase Sapphire Preferred account has 50,000 Ultimate Rewards points expiring on October 31, 2025. Redeem now for travel, cashback, or gift cards."
            },
            {
                "id": "demo_2",
                "subject": "Netflix Subscription Renewed - $15.49 Charged",
                "from": "info@netflix.com",
                "snippet": "Your Netflix Standard plan has been renewed for $15.49.",
                "body": "Your Netflix Standard (with ads) subscription has been renewed and $15.49 has been charged to your Visa card ending 4242."
            },
            {
                "id": "demo_3",
                "subject": "HDFC Bank: 10% Cashback on Amazon — This Weekend Only",
                "from": "offers@hdfcbank.com",
                "snippet": "Use your HDFC Millennia card on Amazon and get 10% instant cashback up to Rs. 1,500.",
                "body": "Dear Customer, Enjoy 10% instant cashback (up to Rs. 1,500) when you shop on Amazon.in this weekend using your HDFC Millennia Credit Card. Offer valid Apr 5-7, 2025."
            },
            {
                "id": "demo_4",
                "subject": "Reminder: Your SBI Card statement is ready",
                "from": "cards@sbi.co.in",
                "snippet": "Your SBI SimplyCLICK Card bill of Rs. 8,240 is due on April 15.",
                "body": "Dear Cardholder, Your SBI SimplyCLICK Credit Card statement for March 2025 is ready. Total amount due: Rs. 8,240. Minimum due: Rs. 412. Due date: April 15, 2025."
            },
            {
                "id": "demo_5",
                "subject": "Earn 5x Miles on Your Next Indigo Flight - Axis Bank",
                "from": "offers@axisbank.com",
                "snippet": "Book Indigo flights with your Axis Bank Vistara card and earn 5x miles.",
                "body": "Exclusive Offer: Use your Axis Bank Vistara Infinite Credit Card to book IndiGo flights and earn 5x Edge Miles. Valid on bookings of Rs. 5,000 or more. Offer valid through April 30, 2025."
            }
        ]

    async def extract_structured_data(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses Gemini Flash (or keyword rules) to extract structured reward/subscription data.
        """
        from src.core.vertex_init import extract_with_gemini

        content = f"Subject: {email['subject']}\nBody: {email['body'] or email['snippet']}"

        prompt = f"""
You are a financial intelligence parser. Analyze this email and extract structured data.
Return ONLY a valid JSON object with these exact keys:
{{
  "type": "REWARD" | "SUBSCRIPTION" | "CASHBACK_OFFER" | "STATEMENT" | "IRRELEVANT",
  "program": "name of card/program (e.g. Chase Sapphire, HDFC Millennia)",
  "amount": numeric value or null,
  "currency": "INR" | "USD" | null,
  "expiry_date": "date string or null",
  "merchant": "merchant name or null",
  "offer_detail": "one-line description of the offer",
  "erv_estimate": estimated rupee/dollar value to user (numeric or null)
}}

Email to analyze:
{content}
"""
        fallback = _keyword_extract(email)
        return await extract_with_gemini(prompt, fallback=fallback)

    async def parse_inbox(self) -> List[Dict[str, Any]]:
        """Full pipeline: Fetch → Extract → Filter → Return structured results."""
        emails = await self.fetch_emails()
        results = []
        for email in emails:
            extracted = await self.extract_structured_data(email)
            if extracted.get("type", "IRRELEVANT") != "IRRELEVANT":
                extracted["source_subject"] = email["subject"]
                extracted["source_from"] = email["from"]
                results.append(extracted)
        return results


def _keyword_extract(email: Dict[str, Any]) -> Dict[str, Any]:
    """Simple keyword-based fallback extractor when Gemini is unavailable."""
    text = f"{email['subject']} {email['snippet']}".lower()

    if "points" in text or "miles" in text or "rewards" in text:
        amt = None
        m = re.search(r"([\d,]+)\s*points", text)
        if m:
            amt = int(m.group(1).replace(",", ""))
        return {
            "type": "REWARD",
            "program": email.get("from", "Unknown"),
            "amount": amt,
            "currency": None,
            "expiry_date": None,
            "merchant": None,
            "offer_detail": email["snippet"][:100],
            "erv_estimate": round(amt / 100, 2) if amt else None
        }
    elif "subscription" in text or "renewed" in text or "charged" in text:
        amt = None
        m = re.search(r"[\$₹rs\.]+\s*([\d,]+\.?\d*)", text)
        if m:
            amt = float(m.group(1).replace(",", ""))
        return {
            "type": "SUBSCRIPTION",
            "program": None,
            "amount": amt,
            "currency": "USD" if "$" in text else "INR",
            "expiry_date": None,
            "merchant": email.get("from", "").split("@")[-1].split(".")[0].title() if "@" in email.get("from", "") else None,
            "offer_detail": email["snippet"][:100],
            "erv_estimate": None
        }
    elif "cashback" in text or "instant discount" in text or "offer" in text:
        return {
            "type": "CASHBACK_OFFER",
            "program": None,
            "amount": None,
            "currency": None,
            "expiry_date": None,
            "merchant": None,
            "offer_detail": email["snippet"][:100],
            "erv_estimate": None
        }
    return {"type": "IRRELEVANT"}


# Global singleton
gmail_parser = GmailRewardParser()
