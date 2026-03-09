
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class ToxicityScorer:
    def __init__(self, device='cuda'):
        self.device = device
        # Check local path first, then fallback to hub
        local_path = "models/toxic-bert"
        if os.path.exists(local_path):
            self.model_name = local_path
            print(f"Loading toxicity scorer from local path: {self.model_name}")
        else:
            self.model_name = "unitary/toxic-bert"
            print(f"Loading toxicity scorer from Hub: {self.model_name}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Warning: Could not load toxicity scorer ({e}). Scores will be -1.")
            self.model = None

    def score(self, texts):
        if self.model is None or not texts:
            return [-1.0] * len(texts)
        
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.sigmoid(outputs.logits)
            # toxic-bert output: [toxic, severe_toxic, obscene, threat, insult, identity_hate]
            # We usually take the max or the first dimension (toxicity)
            toxicity = probs[:, 0].cpu().numpy().tolist()
        return toxicity
