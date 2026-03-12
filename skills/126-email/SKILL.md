---
name: 126-email
emoji: 📧
description: Manage the user's personal 126.com email natively for academic and general correspondence.
metadata:
  {
    "openclaw":
      { "requires": { "bins": ["python3"], "env": ["EMAIL_126_USER", "EMAIL_126_PASS"] } },
  }
---

# 126 Email Assistant

A specialized skill for OpenClaw to handle communications via the user's 126.com email account.

## Tools

### `email_126_read_unread`

Fetch the latest unread emails from the 126 inbox.

- **limit** (integer, optional): Maximum number of emails to retrieve (default: 5).

**Usage**:

```bash
python3 skills/shared/email_tool.py --provider 126 read --limit 3
```

### `email_126_send`

Send an email using the 126 account.

- **to** (string, required): Recipient email address.
- **subject** (string, required): Email subject.
- **body** (string, required): Email content (plain text).

**Usage**:

```bash
python3 skills/shared/email_tool.py --provider 126 send --to "collaborator@university.edu" --subject "Status" --body "..."
```

## [Anti-Hallucination]

- **The Native Extension Mandate**: You are strictly PROHIBITED from fabricating Python scripts in `/tmp` to read, send, or search emails. You MUST use or extend `~/openclaw/skills/shared/email_tool.py` directly. Do NOT bypass the official tooling structure!
