import torch
import os

# Enforce strict offline mode since weights are already cached
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from transformers import AutoProcessor, SeamlessM4Tv2Model
import scipy.io.wavfile

# --- Settings ---
# Use SeamlessM4T v2 Large for V2V
V2V_MODEL_ID = "facebook/seamless-m4t-v2-large"
# Use MMS-TTS for specialized, fast TTS
TTS_MODEL_ID = "facebook/mms-tts-eng" # Can be tuned per lang

# Use standard download method
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
# Ensure the mirror is used if the environment variable is passed
if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["tts", "v2v"], required=True)
    parser.add_argument("--text", help="Text for TTS")
    parser.add_argument("--input", help="Path to input wav for V2V")
    parser.add_argument("--output", required=True, help="Path to output wav")
    parser.add_argument("--src_lang", default="eng")
    parser.add_argument("--tgt_lang", default="cmn") # Default to Mandarin
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if args.action == "tts":
        print(f"Loading MMS TTS model {TTS_MODEL_ID} on {device}...")
        from transformers import VitsModel, VitsTokenizer
        tokenizer = VitsTokenizer.from_pretrained(TTS_MODEL_ID, local_files_only=True)
        model = VitsModel.from_pretrained(TTS_MODEL_ID, local_files_only=True).to(device)
        
        if not args.text:
            print("Error: --text required for tts")
            sys.exit(1)
            
        print(f"Synthesizing: {args.text}")
        inputs = tokenizer(text=args.text, return_tensors="pt").to(device)
        with torch.no_grad():
            output = model(**inputs).waveform
        audio_array_gen = output.cpu().numpy().squeeze()
        sample_rate = model.config.sampling_rate

    elif args.action == "v2v":
        print(f"Loading SeamlessM4T model {V2V_MODEL_ID} on {device}...")
        processor = AutoProcessor.from_pretrained(V2V_MODEL_ID, local_files_only=True)
        model = SeamlessM4Tv2Model.from_pretrained(V2V_MODEL_ID, local_files_only=True).to(device)
        
        if not args.input or not os.path.exists(args.input):
            print(f"Error: input file {args.input} not found")
            sys.exit(1)
            
        print(f"Processing V2V: {args.input}")
        import librosa
        audio, orig_sr = librosa.load(args.input, sr=16000)
        audio_inputs = processor(audio=audio, return_tensors="pt").to(device)
        audio_array_gen = model.generate(**audio_inputs, tgt_lang=args.tgt_lang)[0].cpu().numpy().squeeze()
        sample_rate = model.config.sampling_rate

    scipy.io.wavfile.write(args.output, rate=sample_rate, data=audio_array_gen)
    print(f"Successfully saved to {args.output}")

if __name__ == "__main__":
    main()
