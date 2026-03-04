---
name: school-email
emoji: 🎓
description: Manage the user's university email accounts (e.g. jhun.edu.cn) natively for academic correspondence.
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["python3"], "env": ["ACADEMIC_EMAIL_USER", "ACADEMIC_EMAIL_PASS"] },
      },
  }
---

# School Email Assistant

A specialized skill for OpenClaw to handle communications via the user's university email account.

## Tools

### `email_school_read_unread`

Fetch the latest unread emails from the university inbox.

- **limit** (integer, optional): Maximum number of emails to retrieve (default: 5).

**Usage**:

```bash
python3 skills/shared/email_tool.py --provider school read --limit 3
```

### `email_school_send`

Send an email using the university account.

- **to** (string, required): Recipient email address.
- **subject** (string, required): Email subject.
- **body** (string, required): Email content (plain text).

**Usage**:

```bash
python3 skills/shared/email_tool.py --provider school send --to "collaborator@university.edu" --subject "Status" --body "..."
```

### `email_school_delete_by_id`

Delete a specific email from the university inbox using its exact IMAP ID (obtainable via the `read` command). This ensures surgical precision when cleaning up test messages.

- **id** (string, required): The exact IMAP sequence ID of the email to delete.

**Usage**:

1. First, fetch emails to find the ID:
   `python3 skills/shared/email_tool.py --provider school read --limit 3`
   _(Wait for the JSON output containing `"id": "42"`)_

2. Then, delete that exact email:

```bash
python3 skills/shared/email_tool.py --provider school delete --id 42
```
