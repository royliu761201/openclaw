import os
import io
import argparse
import scipy.io.wavfile
import librosa
import torch
import uvicorn
import asyncio
import concurrent.futures
import time
import gc
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from transformers import AutoProcessor, SeamlessM4Tv2Model

# Enforce strict offline mode since weights are already cached
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Use SeamlessM4T v2 Large for V2V
V2V_MODEL_ID = "facebook/seamless-m4t-v2-large"

app = FastAPI(title="Meta Seamless V2V API")

# Global variables for caching
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = None
model = None

# Idle watchdog configuration
LAST_USED_TIME = time.time()
IDLE_TIMEOUT_SECONDS = 300 # Wait 5 minutes before releasing GPU VRAM
WATCHDOG_INTERVAL = 30 # Check every 30 seconds

def load_models_if_needed():
    """Lazily load models into GPU if they were released."""
    global processor, model
    if model is None or processor is None:
        print(f"Loading SeamlessM4T model {V2V_MODEL_ID} on {device}...")
        processor = AutoProcessor.from_pretrained(V2V_MODEL_ID, local_files_only=True)
        model = SeamlessM4Tv2Model.from_pretrained(V2V_MODEL_ID, local_files_only=True).to(device)
        print("Model loaded into VRAM.")

def release_models():
    """Completely nuke models from memory and clear PyTorch CUDA caching."""
    global processor, model
    if model is not None or processor is not None:
        print("Idle timeout reached. Stripping models from VRAM...")
        
        # 1. Delete explicit refs
        del model
        model = None
        
        del processor
        processor = None
        
        # 2. Force Python garbage collection
        gc.collect()
        
        # 3. Completely return CUDA VRAM to OS
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        print("Models successfully unloaded. GPU is totally free.")

async def idle_watchdog_task():
    """Background asyncio loop that checks if the server is idle."""
    while True:
        await asyncio.sleep(WATCHDOG_INTERVAL)
        if model is not None and (time.time() - LAST_USED_TIME > IDLE_TIMEOUT_SECONDS):
            release_models()

@app.on_event("startup")
async def startup_event():
    # Don't load the model on startup! Waste of resources if not in use.
    # Just start the idle watchdog so it can tear down future models
    asyncio.create_task(idle_watchdog_task())
    print(f"V2V Daemon started. Models will be loaded on-demand and released after {IDLE_TIMEOUT_SECONDS}s of inactivity.")

# Create thread pool to limit concurrent GPU executions and prevent blocking the async loop
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def _process_audio_sync(audio_bytes: bytes, tgt_lang: str) -> str:
    global LAST_USED_TIME
    
    # 1. Load weights dynamically (will be fast if already loaded)
    load_models_if_needed()
    
    # 2. Update heartbeat before heavy processing
    LAST_USED_TIME = time.time()
    # Librosa can load from a BytesIO stream via PySoundFile
    audio, orig_sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    
    print("Processing audio through SeamlessM4T...")
    # Move tensor to device
    audio_inputs = processor(audio=audio, return_tensors="pt").to(device)
    
    with torch.no_grad():
        audio_array_gen = model.generate(**audio_inputs, tgt_lang=tgt_lang)[0].cpu().numpy().squeeze()
        
    sample_rate = model.config.sampling_rate
    
    # Generate unique output path per request
    output_path = f"/tmp/v2v_out_{id(audio_bytes)}.wav"
    scipy.io.wavfile.write(output_path, rate=sample_rate, data=audio_array_gen)
    # Update heartbeat after logic finishes to reset the idle timer
    LAST_USED_TIME = time.time()
    
    return output_path

@app.get("/status")
async def get_status():
    """Tiny endpoint to check if the GPU is currently holding the model."""
    is_loaded = (model is not None)
    idle_time = int(time.time() - LAST_USED_TIME) if is_loaded else 0
    return JSONResponse({
        "gpu_hot": is_loaded,
        "seconds_idle_since_last_use": idle_time,
        "timeout_config": IDLE_TIMEOUT_SECONDS
    })

@app.post("/v2v")
async def generate_v2v(
    audio_file: UploadFile = File(...),
    tgt_lang: str = Form("cmn")
):
    """
    Process an uploaded audio file and return the translated/resynthesized audio.
    """
    print(f"Received V2V request. Target Language: {tgt_lang}")
    
    audio_bytes = await audio_file.read()
    
    # Offload heavy synchronous inference to thread pool
    loop = asyncio.get_running_loop()
    output_path = await loop.run_in_executor(
        executor, 
        _process_audio_sync, 
        audio_bytes, 
        tgt_lang
    )
    
    print(f"Successfully processed audio. Returning {output_path}")
    return FileResponse(output_path, media_type="audio/wav", filename="result.wav")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run V2V FastAPI Server")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface")
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)
