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

import imaplib
import email
from email.header import decode_header
import asyncio

class GmailRewardParser:
    def __init__(self):
        pass

    def _get_credentials(self):
        from src.api.v1_routes import _user_settings
        return _user_settings.get("gmail_email"), _user_settings.get("gmail_password")

    async def fetch_emails(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """Fetches real emails from Gmail matching the reward/subscription query using IMAP."""
        email_addr, password = self._get_credentials()
        if not email_addr or not password:
            print("WARNING: Gmail ID or App Password not provided.")
            return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_sync, email_addr, password, max_results)

    def _fetch_sync(self, email_addr, password, max_results):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(email_addr, password)
            mail.select("inbox")

            status, messages = mail.uid('search', None, 'X-GM-RAW', '"reward OR points OR cashback OR expiring OR subscription OR renewal OR \\"credit card offer\\" OR statement OR miles"')

            emails_list = []
            if status == "OK" and messages[0]:
                msgs = messages[0].split()
                # Get the latest `max_results` messages
                for uid in reversed(msgs[-max_results:]):
                    res, msg_data = mail.uid('fetch', uid, "(RFC822)")
                    if res != "OK":
                        continue
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = msg["Subject"] or ""
                            decoded = decode_header(subject)[0]
                            if isinstance(decoded[0], bytes):
                                subject = decoded[0].decode(decoded[1] if decoded[1] else "utf-8", errors="ignore")
                            
                            sender = msg.get("From", "")
                            decoded_sender = decode_header(sender)[0]
                            if isinstance(decoded_sender[0], bytes):
                                sender = decoded_sender[0].decode(decoded_sender[1] if decoded_sender[1] else "utf-8", errors="ignore")
                            
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    ctype = part.get_content_type()
                                    cdispo = str(part.get("Content-Disposition"))
                                    if ctype in ("text/plain", "text/html") and "attachment" not in cdispo:
                                        try:
                                            body += part.get_payload(decode=True).decode(errors="ignore") + " "
                                        except:
                                            pass
                            else:
                                try:
                                    body = msg.get_payload(decode=True).decode(errors="ignore")
                                except:
                                    pass

                            emails_list.append({
                                "id": uid.decode(),
                                "subject": subject,
                                "from": sender,
                                "snippet": body[:200].replace("\n", " ").strip(),
                                "body": body[:2000]
                            })

            mail.logout()
            return emails_list
        except Exception as e:
            print(f"Gmail IMAP fetch error: {e}")
            return []

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
