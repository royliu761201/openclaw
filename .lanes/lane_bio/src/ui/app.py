import streamlit as st
import os
import sys
import asyncio
import re

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.model_client import ModelClient
from config import ModelTier

st.set_page_config(page_title="Refactored Research Bot Dashboard", layout="wide", page_icon="🧪")

st.title("🧪 AI4S Autonomous Scientist (Dashboard)")

# Connect to Journal
JOURNAL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../research_vault/journal.md"))

from skills.patent_writer import PatentWriter
from skills.grant_writer import GrantWriter
from skills.paper_writer import PaperWriter
from skills.scenario_writer import ScenarioWriter

# Tabs
tab_chat, tab_journal, tab_academic, tab_control = st.tabs(["💬 Discuss Ideas", "📓 Research Journal", "🏛️ Academic Center", "⚙️ Control Panel"])

# --- TAB 1: DISCUSSION ---
with tab_chat:
    st.header("Brainstorming & Task Initiation")
    
    # Init Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                 st.markdown(message["content"])
            else:
                 st.markdown("*(Multimodal Content Uploaded)*")

    # File Uploader
    uploaded_file = st.file_uploader("Upload context (PDF/Image/Word/Text)", type=["png", "jpg", "jpeg", "pdf", "tex", "md", "txt", "csv", "docx"])
    
    # Chat Logic
    if prompt := st.chat_input("What would you like to research?"):
        
        # Prepare Content
        user_content = [prompt]
        display_content = prompt
        
        if uploaded_file:
            bytes_data = uploaded_file.getvalue()
            file_type = uploaded_file.type
            file_name = uploaded_file.name
            ext = file_name.split(".")[-1].lower()
            
            from google.genai import types

            # 1. Image/PDF -> Native Multimodal
            if ext in ["png", "jpg", "jpeg", "pdf"]:
                 # Create Part
                 part = types.Part.from_bytes(data=bytes_data, mime_type=file_type)
                 user_content.append(part)
                 display_content += f"\n\n📎 **Attachment (Visual/PDF)**: `{file_name}`"

            # 2. Excel/CSV/Text/MD/Tex -> Text Context
            elif ext in ["csv", "txt", "md", "tex", "py", "json"]:
                 try:
                     text_data = bytes_data.decode("utf-8")
                     user_content[0] += f"\n\n--- FILE: {file_name} ---\n{text_data}\n--- END FILE ---\n"
                     display_content += f"\n\n📎 **Attachment (Text)**: `{file_name}`"
                 except Exception as e:
                     st.error(f"Error decoding text file: {e}")

            # 3. Word (Docx) -> Text Context via python-docx
            elif ext == "docx":
                 try:
                     import docx
                     from io import BytesIO
                     doc = docx.Document(BytesIO(bytes_data))
                     full_text = []
                     for para in doc.paragraphs:
                         full_text.append(para.text)
                     text_data = "\n".join(full_text)
                     user_content[0] += f"\n\n--- FILE: {file_name} ---\n{text_data}\n--- END FILE ---\n"
                     display_content += f"\n\n📎 **Attachment (Word)**: `{file_name}`"
                 except Exception as e:
                     st.error(f"Error reading Docx: {e}")
            
            else:
                 st.warning(f"Unsupported file type: {ext}")
                 
            # Persistence for Tab 3
            if len(user_content) > 1: # user_content is [prompt, part] or [text_with_file_content]
                st.session_state['last_uploaded_content'] = user_content
                st.success(f"File '{file_name}' ready for Academic Output.")

        # Add User output
        st.session_state.messages.append({"role": "user", "content": display_content})
        with st.chat_message("user"):
            st.markdown(display_content)

        # Bot Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Direct Logic (No API for speed)
                client = ModelClient()
                
                # System Prompt for Extraction
                system_prompt = """
                You are the ResearchBot Manager.
                1. Discuss the user's research idea.
                2. Analyze any uploaded images/PDFs for inspiration.
                3. If it's a solid research task, output: [TASK] <Topic Name> | <Description>
                4. Be concise and encouraging.
                """
                
                async def get_response():
                    # Pass list if attachment exists, else string
                    msg_payload = user_content if uploaded_file else prompt
                    return await client.chat(msg_payload, system_instruction=system_prompt)
                
                response_text = asyncio.run(get_response())
                
                # Parse Task
                tasks = []
                clean_response = response_text
                
                if "[TASK]" in response_text:
                    parts = response_text.split("[TASK]")
                    clean_response = parts[0]
                    # Extract tasks
                    task_lines = parts[1:]
                    for line in task_lines:
                        # Simple parse
                        t_parts = line.split("|")
                        if len(t_parts) >= 1:
                            tasks.append(t_parts[0].strip())
                            
                    # Append to Journal
                    if tasks and os.path.exists(JOURNAL_PATH):
                        with open(JOURNAL_PATH, "a") as f:
                            for t in tasks:
                                f.write(f"\n- [ ] **{t}** (Multimodal Add) <!-- status: pending -->")
                        clean_response += f"\n\n✅ **Added {len(tasks)} task(s) to Journal:**\n" + "\n".join([f"- {t}" for t in tasks])

                full_response = clean_response
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"Error: {e}"
                message_placeholder.error(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- TAB 2: JOURNAL ---
with tab_journal:
    st.header("Research Journal & Tasks")
    if os.path.exists(JOURNAL_PATH):
        with open(JOURNAL_PATH, "r") as f:
            st.markdown(f.read())
    else:
        st.info("No journal found yet.")

# --- TAB 3: ACADEMIC CENTER ---
with tab_academic:
    st.header("🏛️ Academic Output Center")
    st.info("Unified Engine for Parallel Research Output. Generate Papers, Patents, Grants, and Products simultaneously.")
    
    # 1. Global Project Context
    st.subheader("1. Project Context")
    col_input1, col_input2 = st.columns([1, 1])
    with col_input1:
        topic = st.text_input("Research Topic / Title", value="Quantum-Enhanced Transformers", key="acad_topic")
    with col_input2:
        context = st.text_area("Research Context / Abstract", height=150, placeholder="Paste your abstract...", key="acad_context")
    
    # context injection
    effective_context = context
    if 'last_uploaded_content' in st.session_state:
        use_uploads = st.checkbox("📎 Include Uploaded File Context (from Discussion Tab)", value=True)
        if use_uploads and len(st.session_state['last_uploaded_content']) > 1:
            # Combine text context with uploaded parts (skipping the prompt str at index 0)
            file_parts = st.session_state['last_uploaded_content'][1:]
            effective_context = [context] + file_parts
            st.info(f"✅ Context augmented with {len(file_parts)} uploaded file parts.")

    # 2. Target Outputs
    st.subheader("2. Target Outputs")
    col_sel1, col_sel2 = st.columns([1, 2])
    
    with col_sel1:
        target_outputs = st.multiselect(
            "Select Artifacts to Generate:",
            ["Academic Paper", "Patent Disclosure", "Grant Proposal", "Product Scenario"],
            default=["Academic Paper", "Patent Disclosure"]
        )
    
    with col_sel2:
        # Conditional Inputs
        grant_constraints = ""
        if "Grant Proposal" in target_outputs:
            grant_constraints = st.text_area("💰 Grant Guidelines (Constraints)", height=68, value="Budget: 500k. Limit: 4 Years.")

    # 3. Action
    if st.button("🚀 Launch Parallel Research Engine", type="primary"):
        if not topic or not context:
            st.error("Please provide both Topic and Context.")
        else:
            with st.status(f"Generating {len(target_outputs)} Research Artifacts...", expanded=True) as status:
                
                async def run_parallel_generation():
                    tasks = []
                    
                    # Initialize Writers
                    path_collectors = []
                    
                    if "Academic Paper" in target_outputs:
                        st.write("📄 initializing PaperWriter...")
                        # Pass effective_context (str or list)
                        tasks.append(PaperWriter().draft_paper(topic, effective_context))
                        path_collectors.append("Paper")
                        
                    if "Patent Disclosure" in target_outputs:
                        st.write("📜 initializing PatentWriter...")
                        tasks.append(PatentWriter().draft_disclosure(topic, effective_context))
                        path_collectors.append("Patent")
                        
                    if "Grant Proposal" in target_outputs:
                        st.write("💰 initializing GrantWriter...")
                        tasks.append(GrantWriter().draft_proposal(topic, effective_context, grant_constraints))
                        path_collectors.append("Grant")
                        
                    if "Product Scenario" in target_outputs:
                        st.write("💡 initializing ScenarioWriter...")
                        tasks.append(ScenarioWriter().draft_scenario_package(topic, effective_context))
                        path_collectors.append("Scenario")
                    
                    # Run All
                    results = await asyncio.gather(*tasks)
                    return dict(zip(path_collectors, results))

                try:
                    # Run Async
                    import asyncio
                    import shutil
                    from datetime import datetime
                    
                    results_dict = asyncio.run(run_parallel_generation())
                    
                    st.session_state['generation_results'] = results_dict
                    
                    status.update(label="All Research Tasks Complete!", state="complete")
                    
                except Exception as e:
                    st.error(f"Parallel Generation Failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # 4. Independent Artifact Downloads
    if 'generation_results' in st.session_state:
        st.divider()
        st.success("🎉 Research Artifacts Ready")
        
        # Display separate buttons
        res_cols = st.columns(len(st.session_state['generation_results']))
        
        for idx, (r_type, r_path) in enumerate(st.session_state['generation_results'].items()):
            with res_cols[idx]:
                if r_path and os.path.exists(r_path):
                     with open(r_path, "rb") as f:
                        st.download_button(
                            label=f"📦 Download {r_type} Package",
                            data=f,
                            file_name=os.path.basename(r_path),
                            mime="application/zip",
                            key=f"dl_{r_type}"
                        )
                else:
                    st.warning(f"{r_type} Generation Failed")

# --- TAB 4: CONTROL ---
with tab_control:
    st.header("Daemon Control")
    st.info("To start the Autonomous Daemon, run `python3 run_autonomous.py` in your terminal.")
    
    st.subheader("Configuration")
    st.code("""
# src/research_bot/config.py
MODEL_POOL = {
    "CRITICAL": "gemini-3-flash-preview",
    "STANDARD": "gemini-2.5-flash-lite"
}
    """, language="python")
