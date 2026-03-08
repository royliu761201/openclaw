import os
import sys
import json
import argparse
import subprocess
import google.generativeai as genai

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key: return key
    key_path = os.path.expanduser("~/.gemini/api_key")
    if os.path.exists(key_path):
        with open(key_path, "r") as f:
            return f.read().strip()
    return None

def generate_ppt(json_data_str, output_path):
    print(f"Generating PPT -> {output_path}")
    ppt_script = "/Users/roy-jd/openclaw_podman_test/skills/ppt-maker/gen_ppt.py"
    if not os.path.exists(ppt_script):
        print(f"[Error] PPT Maker skill not found at {ppt_script}")
        return
    try:
        subprocess.run([sys.executable, ppt_script, "--data", json_data_str, "--output", output_path], check=True)
    except Exception as e:
        print(f"[Error] PPT Generation failed: {e}")

def get_mime_type(file_path):
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf': return 'application/pdf'
    if ext in ['png', 'jpg', 'jpeg', 'webp']: return f'image/{ext}'
    if ext == 'docx': return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if ext == 'pptx': return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    if ext == 'txt': return 'text/plain'
    if ext == 'md': return 'text/markdown'
    return None

def main():
    parser = argparse.ArgumentParser(description="OpenClaw NotebookLM (Powered by Gemini File API)")
    parser.add_argument("--files", nargs='+', help="PDF/Word/PPTX/TXT/Images to load into memory", required=False)
    parser.add_argument("--query", type=str, help="Global query to the documents", required=True)
    parser.add_argument("--ppt", type=str, help="Output structured PPT summary", required=False)
    parser.add_argument("--model", type=str, default="gemini-3.1-flash-lite-preview", help="LLM model (default: gemini-3.1-flash-lite-preview)")
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        print("[Auth Error] GEMINI_API_KEY not found in ~/.gemini/api_key")
        sys.exit(1)

    genai.configure(api_key=api_key)
    
    uploaded_files = []
    if args.files:
        print(f"Uploading {len(args.files)} files into {args.model} memory...")
        for path in args.files:
            if not os.path.exists(path):
                print(f"[Warning] File not found: {path}")
                continue
            try:
                mime_type = get_mime_type(path)
                print(f"  -> Uploading {os.path.basename(path)} " + (f"({mime_type})" if mime_type else ""))
                if mime_type:
                    f = genai.upload_file(path=path, mime_type=mime_type)
                else:
                    f = genai.upload_file(path=path)
                uploaded_files.append(f)
            except Exception as e:
                print(f"  [Error] Failed to upload {path}: {e}")

    model = genai.GenerativeModel(model_name=args.model)
    
    prompt = args.query
    if args.ppt:
        prompt += """
        
OUTPUT FORMAT INSTRUCTION (STRICT):
Because the user requested a PPT presentation, you MUST output ONLY valid JSON that matches this structure perfectly. Do not output markdown code blocks.
{
  "title": "Main Presentation Title",
  "pages": [
    {
      "title": "Slide Title 1",
      "bullets": ["Bullet 1", "Bullet 2"]
    }
  ]
}
"""

    contents = uploaded_files + [prompt]
    
    print("\n[NotebookLM] Synthesizing context with Gemini...")
    try:
        response = model.generate_content(contents)
        text_out = response.text.strip()
        
        if args.ppt:
            if text_out.startswith("```json"):
                text_out = text_out[7:-3].strip()
            elif text_out.startswith("```"):
                text_out = text_out[3:-3].strip()
            # Basic cleanup if the model included leading/trailing junk
            import re
            json_match = re.search(r'\{.*\}', text_out, re.DOTALL)
            if json_match:
                text_out = json_match.group(0)
            generate_ppt(text_out, args.ppt)
        else:
            print("\n" + "="*50)
            print(f"NotebookLM Insights (via {args.model}):")
            print("="*50)
            print(text_out)
            print("="*50 + "\n")
            
    except Exception as e:
        print(f"[Error] Generation failed: {e}")
        
    for f in uploaded_files:
        try:
            genai.delete_file(f.name)
        except:
            pass

if __name__ == "__main__":
    main()
