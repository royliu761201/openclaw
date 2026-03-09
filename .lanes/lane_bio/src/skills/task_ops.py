import os
import datetime

def update_task_status(journal_path: str, idea_id: str, topic: str, step: str, status: str):
    """
    Atomic Operation: Updates the row for `idea_id` in the Active Cycles table in journal.md.
    """
    if not os.path.exists(journal_path):
        print(f"[TaskOps] Error: {journal_path} not found.")
        return

    print(f"[TaskOps] Updating {idea_id}: {step} -> {status}")

    with open(journal_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_table = False
    updated = False
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row_str = f"| {idea_id} | {topic} | {status} | {step} | {timestamp} |\n"

    for line in lines:
        if "| ID | Topic |" in line:
            in_table = True
            new_lines.append(line)
            # Ensure separator line follows
            if lines.index(line) + 1 < len(lines):
                 sep = lines[lines.index(line)+1]
                 if set(sep.strip()) <= {'|', '-', ' ', ':'}:
                     # It's likely the separator, we will append it in next loop or manually here if we skip
                     pass
            continue
        
        if in_table and line.strip().startswith("|"):
            # Check if this row is our idea
            if f"| {idea_id} |" in line:
                new_lines.append(row_str)
                updated = True
            elif set(line.strip()) <= {'|', '-', ' ', ':'}:
                 # Separator line, keep it
                 new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            if in_table and line.strip() == "":
                in_table = False
                if not updated:
                    # Append new row if table ended and we didn't find it
                    new_lines.insert(len(new_lines) - (1 if new_lines[-1].strip() == "" else 0), row_str) 
                    updated = True
            new_lines.append(line)
    
    # If table was empty or we are still in table at EOF
    if not updated and in_table:
         new_lines.append(row_str)

    with open(journal_path, "w") as f:
        f.writelines(new_lines)

def init_board(journal_path: str):
    """
    Atomic Operation: Ensures board exists with header.
    """
    if not os.path.exists(journal_path):
        os.makedirs(os.path.dirname(journal_path), exist_ok=True)
        with open(journal_path, 'w') as f:
            f.write("# Research Journal\n\n## Active Cycles\n\n| ID | Topic | Status | Step | Updated |\n|---|---|---|---|---|\n")
