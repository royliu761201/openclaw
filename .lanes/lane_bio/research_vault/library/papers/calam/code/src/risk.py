import torch
import torch.nn as nn

class RiskMonitor:
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.Tensor:
        """
        Returns a risk score between [0, 1] for each sequence in the batch.
        """
        raise NotImplementedError

class KeywordRiskMonitor(RiskMonitor):
    def __init__(self, tokenizer, keywords):
        self.tokenizer = tokenizer
        self.keywords = set(keywords)
        self.keyword_ids = set()
        for kw in keywords:
            # Simple encoding, might need refinement for subwords
            ids = tokenizer.encode(kw, add_special_tokens=False)
            if ids:
                self.keyword_ids.add(ids[0]) 

    def __call__(self, input_ids, scores):
        # Heuristic: Check if recently generated tokens match keywords
        # Or look at the logits of the *next* token to see if high prob tokens are risky (Lookahead)
        
        batch_size = scores.shape[0]
        risk_scores = torch.zeros(batch_size, device=scores.device)
        
        # Lookahead: Check if top-k predictions contain risky tokens
        probs = torch.softmax(scores, dim=-1)
        top_probs, top_indices = torch.topk(probs, k=5, dim=-1)
        
        for i in range(batch_size):
            risk = 0.0
            for idx, p in zip(top_indices[i], top_probs[i]):
                if idx.item() in self.keyword_ids:
                    risk += p.item()
            
            # Normalize or clip
            risk_scores[i] = min(risk * 5.0, 1.0) # Scale up sensitivity
            
        return risk_scores

class RandomRiskMonitor(RiskMonitor):
    """
    Random baseline for testing infrastructure.
    """
    def __call__(self, input_ids, scores):
        return torch.rand(input_ids.shape[0], device=input_ids.device)
