import os
import subprocess
import shutil
import asyncio
from typing import Dict, List, Optional, Any
from .base_skill import BaseSkill

class VisualInspector(BaseSkill):
    """
    Skill for visual quality assurance of generated PDFs.
    1. Generates Image Previews (PNG).
    2. Analyzes LaTeX logs for Layout Defects (Overfull hboxes).
    """

    def __init__(self, model_client: Optional[Any] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.client = model_client

    def verify(self) -> bool:
        """
        Checks for PDF conversion tools.
        Returns True if 'pdftocairo' (preferred) or 'sips' (fallback) is available.
        """
        has_pdftocairo = shutil.which("pdftocairo") is not None
        has_sips = shutil.which("sips") is not None
        
        if not (has_pdftocairo or has_sips):
            print("[VisualInspector] ❌ Missing PDF tools. Install 'poppler' or use macOS.")
            return False
            
        return True
    
    def inspect_artifact(self, pdf_path: str, log_path: str, output_dir: str, venue: str = "NeurIPS") -> Dict[str, str]:
        """
        Runs full inspection. Returns paths to report and preview image.
        """
        print(f"[VisualInspector] 🔍 Inspecting {os.path.basename(pdf_path)} for {venue}...")
        
        # 1. Generate Preview Image
        preview_path = os.path.join(output_dir, "preview.png")
        self._generate_preview(pdf_path, preview_path)
        
        # 2. Analyze Layout (Logs)
        defects = self._analyze_log(log_path)

        # 3. Visual Critique (VLM)
        critique = ""
        if self.client and os.path.exists(preview_path):
             print(f"[VisualInspector] 👁️ Running Visual Critic on {preview_path}...")
             critique = self.critique_layout(preview_path, venue=venue)
        
        # 4. Generate Report
        report_path = os.path.join(output_dir, "visual_report.md")
        self._write_report(report_path, defects, preview_path, critique)
        
        return {
            "preview": preview_path,
            "report": report_path,
            "defects_count": len(defects),
            "critique": critique
        }

    def critique_layout(self, image_path: str, venue: str = "NeurIPS") -> str:
        """Uses VLM to critique the paper layout against Venue Standards."""
        try:
            from google.genai import types
            from config import ModelTier
            import yaml
            
            # Load Venue Specs
            venue_specs = ""
            try:
                with open("research_vault/knowledge_base/venues.yaml", "r") as f:
                    venues = yaml.safe_load(f)
                    # Simple fuzzy match or direct lookup
                    # Assuming venue key matches or we search
                    # For now, generic fallback if not found
                    if venue in venues:
                        v = venues[venue]
                        venue_specs = f"""
                        Venue: {venue}
                        - Page Limit: {v.get('page_limit', 'Unknown')}
                        - Column Format: {v.get('columns', 'Unknown')} (Check for this!)
                        - Double Blind: {v.get('double_blind', True)} (Ensure no authors listed!)
                        """
            except Exception:
                venue_specs = f"Venue: {venue} (Standard Top-Tier AI Conference)"

            with open(image_path, "rb") as f:
                image_bytes = f.read()
                
            prompt = f"""
            Role: Senior Area Chair for {venue}.
            Task: Critique this paper layout (Page 1 Preview).
            
            {venue_specs}
            
            CRITICAL CHECKS:
            1. **Anonymity**: If Double Blind, are authors hidden?
            2. **Density**: Is space wasted? (Top-tier requires high information density).
            3. **Figures**: Are font sizes too small? (Common rejection reason).
            4. **Structure**: Does the Abstract/Intro look standard?
            
            Output:
            - **Verdict**: [PASS / MINOR ISSUES / REJECT]
            - **Issues**: Bullet points.
            """
            
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            
            print(f"[VisualInspector] 🧠 Asking Gemini Vision to critique for {venue}...")
            response = str(asyncio.run(self.client.chat(
                message=[prompt, image_part],
                tier=ModelTier.CRITICAL,
                task_type="review"
            )))
            return response
            
        except ImportError:
             return "Error: google.genai or pyyaml not installed."
        except Exception as e:
            print(f"[VisualInspector] ⚠️ Visual Critic failed: {e}")
            return f"Critic Error: {e}"

    def _generate_preview(self, pdf_path: str, output_path: str):
        """Tries pdftocairo, falls back to macOS sips."""
        try:
            # Try pdftocairo (Linux/Cross-platform high quality)
            subprocess.run(
                ["pdftocairo", "-png", "-r", "150", "-singlefile", pdf_path, output_path.replace(".png", "")],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                # Fallback to macOS sips
                subprocess.run(
                    ["sips", "-s", "format", "png", pdf_path, "--out", output_path],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                print("[VisualInspector] 📸 Generated preview using macOS sips.")
            except Exception as e:
                print(f"[VisualInspector] ⚠️ Could not generate preview: {e}")

    def _analyze_log(self, log_path: str) -> List[str]:
        """Parses log for Overfull \hbox warnings."""
        defects = []
        if not os.path.exists(log_path): return []
        
        with open(log_path, "r", errors="replace") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            if "Overfull \\hbox" in line:
                # Extract context (next line usually has line numbers)
                context = lines[i+1].strip() if i+1 < len(lines) else ""
                defects.append(f"{line.strip()} | Context: {context}")
                
        return defects

    def _write_report(self, path: str, defects: List[str], preview_path: str, critique: str):
        content = f"""# Visual Inspection Report
        
## 1. Document Preview
![Page 1]({os.path.abspath(preview_path)})

## 2. Layout Analysis
Found {len(defects)} layout defects (Text Overflow).

"""
        if defects:
            content += "### 🚨 Defects (Overfull Box)\n"
            for d in defects:
                content += f"- `{d}`\n"
        else:
            content += "✅ No layout defects found.\n"
            
        if critique:
             content += f"\n## 3. Visual Critique (AI Editor)\n{critique}\n"
             
        with open(path, "w") as f:
            f.write(content)
        print(f"[VisualInspector] 📝 Report written to {path}")
