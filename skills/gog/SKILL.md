---
name: gog
emoji: 🧭
description: CLI interface for Google Workspace (Gmail, Calendar, Drive, Docs)
metadata: { "openclaw": { "requires": { "bins": ["gog"] } } }
---

# `gog` (Google in your terminal) Skill

Use the `gog` command to interact with the user's Google Workspace (Gmail, Calendar, Drive, Docs, Sheets, etc).

## Requirements

If the user hasn't authenticated, instruct them to open their terminal and run:
`gog auth credentials <path_to_client_json>` followed by `gog auth add <their-email>`.

**Important Output Parsing**: For agent processing, append `--json` to `gog` commands (when applicable) to receive a structured JSON response instead of human-oriented tables. Append `--plain` for tab-separated output if `--json` is unavailable or errors out.

## Base Commands

Below are the primary subsystems you can orchestrate. You can stack commands, for example `gog gmail get <message_id>`.

- **`gog time now`**
  Get current local server time in readable text.

- **`gog gmail`**
  Search (`gog gmail search 'newer_than:7d' --max 10`), read threads (`gog gmail thread get <id>`), send emails (`gog gmail send --to x@a.com --subject Y --body Z`), and manage labels/filters.

- **`gog calendar`**
  Check schedules (`gog calendar events primary --today`), see team calendars (`gog calendar team team-alias`), list calendars (`gog calendar calendars`), search events (`gog calendar search "meeting"`), or create/update/delete events.

- **`gog drive`**
  List and search files (`gog drive ls`, `gog drive search "receipt"`), upload/download/organize folders. Note down the `<fileId>` from the output to manipulate documents.

- **`gog docs`** / **`gog sheets`** / **`gog slides`**
  Get details or read components of the Google app formats.
  Examples: `gog docs info <id>`, `gog docs cat <id>`, `gog slides info <id>`.

- **`gog tasks`**
  Get tasks (`gog tasks lists`, `gog tasks list <tasklistId>`).

## Sandboxing & Limits

The tool communicates dynamically over REST APIs using user OAuth credentials. Please be cautious with destructive operations like `gmail send`, `drive delete`, or `calendar delete`. Verify inputs if they arise from untrusted sources.

## Aliases

If the user specifies an email address, you can append `--account <email>` to the end of your command.
