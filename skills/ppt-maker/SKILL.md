---
name: ppt-maker
description: Generate and edit actual .pptx presentation files for academic talks, project defenses, and lectures. Supports stateful partial editing.
metadata:
  openclaw:
    requires:
      python: ">=3.9"
      system: ["graphviz"]
      packages:
        - "python-pptx"
---

# PPT Maker Skill

This skill allows you (OpenClaw) to physically generate `.pptx` PowerPoint files based on the academic content you outline, and critically, supports **stateful partial editing**. You can create pure text slides OR slides with a text-body on the left and a generated topological diagram or artistic image on the right.

## Usage

When a user asks you to "create a PPT", "make a presentation", or "edit the previous slides":

1. **State Persistence**: If this is a new PPT, you MUST first write the presentation structure to a physical JSON file in the user's workspace (e.g., `/Users/roy-jd/Documents/projects/openclaw/workspace/defense_state.json`) using file editing tools. If the user asks for a partial edit, you MUST read this JSON file, modify only the requested parts (e.g., using `replace_file_content`), and save it.

2. **JSON Format**: The JSON must be an object with `"title"` and an array of `"pages"`.

   ```json
   {
     "title": "Main Presentation Title",
     "pages": [
       {
         "title": "Slide 1 (Text Only)",
         "bullets": ["Point A", "Point B"]
       },
       {
         "title": "Slide 2 (With Diagram)",
         "bullets": ["Client requests server", "Server hits DB"],
         "image_dot": "digraph G { Client -> Server -> Database; }"
       },
       {
         "title": "Slide 3 (With Artistic Image)",
         "bullets": ["AI envisions the future", "Lab setting"],
         "image_prompt": "A futuristic glowing laboratory"
       }
     ]
   }
   ```

3. **Execute the Generator**: Use the `run_command` tool to execute `gen_ppt.py`. Use the `--input` flag passing the state file you just created or edited.

```bash
python skills/ppt-maker/gen_ppt.py --input "/Users/roy-jd/Documents/projects/openclaw/workspace/defense_state.json" --output "/Users/roy-jd/Documents/projects/openclaw/workspace/defense.pptx"
```

4. **Return the File**: Tell the user the absolute path of the generated `.pptx` file. If it was an edit, explicitly state exactly which pages/points were successfully modified.
