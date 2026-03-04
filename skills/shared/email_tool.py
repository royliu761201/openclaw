#!/usr/bin/env python3
import os
import sys
import json
import imaplib
import smtplib
import email
from email.message import EmailMessage
from email.header import decode_header
import argparse
from pathlib import Path

def load_credentials(provider=None):
    if provider == "126":
        user_keys = ["EMAIL_126_USER"]
        pass_keys = ["EMAIL_126_PASS"]
    elif provider == "school" or provider == "jhun":
        user_keys = ["ACADEMIC_EMAIL_USER"]
        pass_keys = ["ACADEMIC_EMAIL_PASS"]
    else:
        user_keys = ["ACADEMIC_EMAIL_USER", "EMAIL_126_USER"]
        pass_keys = ["ACADEMIC_EMAIL_PASS", "EMAIL_126_PASS"]

    user = None
    pwd = None
    imap_server = None
    smtp_server = None

    for k in user_keys:
        if os.environ.get(k): user = os.environ.get(k); break
    for k in pass_keys:
        if os.environ.get(k): pwd = os.environ.get(k); break

    if not user or not pwd:
        print(f"Error: Missing credentials for the requested provider '{provider}'. Required env vars: {user_keys} / {pass_keys}")
        sys.exit(1)

    if "@126.com" in user:
        imap_server = "imap.126.com"
        smtp_server = "smtp.126.com"
    elif "@jhun.edu.cn" in user or "exmail.qq.com" in user:
        imap_server = "imap.exmail.qq.com"
        smtp_server = "smtp.exmail.qq.com"
    else:
        print("Error: Unknown domain.")
        sys.exit(1)

    return user, pwd, imap_server, smtp_server

def decode_str(s):
    if not s: return ""
    decoded, charset = decode_header(s)[0]
    if charset:
        try:
            return decoded.decode(charset)
        except:
            return decoded.decode("utf-8", errors="ignore")
    elif isinstance(decoded, bytes):
        return decoded.decode("utf-8", errors="ignore")
    return decoded

def read_emails(user, pwd, imap_server, limit):
    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(user, pwd)
        
        # NetEase anti-spam bypass: identifying the client
        if "126.com" in imap_server or "163.com" in imap_server:
            imaplib.Commands['ID'] = ('AUTH')
            mail._simple_command("ID", '("name" "MacMail" "version" "5.1" "vendor" "Apple" "support-email" "apple@apple.com")')
            
        status, response = mail.select("INBOX")
        if status != "OK":
            print(json.dumps({"error": f"Failed to select INBOX: {response}"}))
            sys.exit(1)

        status, response = mail.search(None, "UNSEEN")
        if status != "OK":
            print(json.dumps({"error": "Failed to search emails"}))
            sys.exit(1)

        email_ids = response[0].split()
        if not email_ids:
            print(json.dumps({"message": "No new unread emails.", "count": 0}))
            return

        emails_data = []
        for e_id in email_ids[-limit:]:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = decode_str(msg.get("Subject", ""))
            sender = decode_str(msg.get("From", ""))
            date = msg.get("Date", "")
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload: body += payload.decode("utf-8", errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload: body = payload.decode("utf-8", errors="ignore")

            emails_data.append({
                "id": e_id.decode('utf-8'),
                "subject": subject,
                "from": sender,
                "date": date,
                "body_preview": body[:1000] if body else ""
            })

        print(json.dumps({"count": len(emails_data), "emails": emails_data}, ensure_ascii=False, indent=2))
        mail.logout()

    except Exception as e:
        print(json.dumps({"error": f"IMAP Error: {e}"}))
        sys.exit(1)


def send_email(user, pwd, smtp_server, to, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to

        server = smtplib.SMTP_SSL(smtp_server, 465, timeout=30)
        server.set_debuglevel(1)  # Uncomment for verbose network logging
        server.login(user, pwd)
        server.send_message(msg)
        server.quit()
        print(json.dumps({"status": "success", "message": f"Email sent successfully to {to}"}))
    except Exception as e:
        print(json.dumps({"error": f"SMTP Error: {e}"}))
        sys.exit(1)

def delete_emails(user, pwd, imap_server, target_id):
    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(user, pwd)
        
        if "126.com" in imap_server or "163.com" in imap_server:
             imaplib.Commands['ID'] = ('AUTH')
             mail._simple_command("ID", '("name" "MacMail" "version" "5.1" "vendor" "Apple" "support-email" "apple@apple.com")')
            
        mail.select("INBOX")
        
        # Directly mark the exact IMAP sequence ID for deletion
        status, response = mail.store(str(target_id), '+FLAGS', '\\Deleted')
        if status != "OK":
            print(json.dumps({"error": f"Failed to mark email {target_id} as deleted. It may not exist."}))
            sys.exit(1)

        mail.expunge()
        print(json.dumps({"status": "success", "message": f"Successfully deleted email ID: {target_id}"}))
        mail.logout()

    except Exception as e:
        print(json.dumps({"error": f"IMAP Error: {e}"}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Academic Email Skill")
    parser.add_argument("--provider", type=str, choices=["126", "school", "jhun"], default=None, help="Email provider to use")
    
    subparsers = parser.add_subparsers(dest="command")

    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("--limit", type=int, default=5, help="Number of unread emails to fetch")

    send_parser = subparsers.add_parser("send")
    send_parser.add_argument("--to", required=True, help="Recipient email")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("--id", required=True, help="Exact IMAP sequence ID of the email to delete (obtainable via 'read' command).")

    args = parser.parse_args()
    user, pwd, imap_server, smtp_server = load_credentials(args.provider)

    if args.command == "read":
        read_emails(user, pwd, imap_server, args.limit)
    elif args.command == "send":
        send_email(user, pwd, smtp_server, args.to, args.subject, args.body)
    elif args.command == "delete":
        delete_emails(user, pwd, imap_server, args.id)
    else:
        parser.print_help()
