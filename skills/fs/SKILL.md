---
name: fs
description: Read, write, and modify files.
metadata: { "openclaw": { "requires": { "bins": ["python"] } } }
---

# File System Skill

Tools for file manipulation.

## Tools

### `read_file`
Read content of a file.

- **path** (string, required): File path.

### `write_file`
Write content to a file (overwrites).

- **path** (string, required): File path.
- **content** (string, required): Content to write.

### `replace_in_file`
Replace text in a file.

- **path** (string, required): File path.
- **old** (string, required): String to replace.
- **new** (string, required): Replacement string.

## Usage

### Read File
```bash
python skills/fs/scripts/fs_tool.py read "workspace/test.txt"
```

### Write File
```bash
python skills/fs/scripts/fs_tool.py write "workspace/test.txt" "Hello World"
```

### Replace Text
```bash
python skills/fs/scripts/fs_tool.py replace "workspace/broken.tex" "\unknowncommand" "% Fixed"
```
