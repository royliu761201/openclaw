---
name: work-assistant
emoji: 💼
description: Personal Work Assistant for scheduling, document management, and general administrative task automation.
metadata:
  openclaw:
    requires:
      skills: ["gemini", "github", "tavily-search", "feishu"]
---

# Work Assistant

This skill provides a structured framework for managing day-to-day work tasks, administrative support, and document organization.

## 1. Schedule & Task Management
**Goal**: Organize meetings, set reminders, and track to-do lists.
- **Tools**: `calendar`, `todo-list`.
- **Logic**: Proactively check for upcoming deadlines and suggest daily priorities based on project status in Git.

## 2. Document & Resource Organization
**Goal**: Maintain the "Clean & Economical" workspace.
- **Scope**: Categorize documents, clean up temporary files, and manage the `roy003_storage` directory.
- **SOP**: "Audit the workspace daily. Identify large files (>100MB) unused for 7 days and suggest migration to Google Drive or deletion."

## 3. Communication Support (Feishu)
**Goal**: Act as a bridge between the user and Feishu integrations.
- **Functionality**: Summarize chat threads, draft formal announcements, and manage bot event triggers.
- **Context**: Access to the `Work Assistant` custom app on Feishu.

## 4. Production Standard (Mac 03)
**CRITICAL**: All stable automation workflows MUST be deployed to Mac 03.
- **Environment**: Use the `openclaw` instance on Mac 03 for production level reliability.
- **SSoT**: Ensure all work logs and configurations are committed to the `research-archive` repository.
