from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import torch.nn.functional as F

class Reward:
    tokenizer = AutoTokenizer.from_pretrained("s-nlp/roberta-base-formality-ranker")
    model = AutoModelForSequenceClassification.from_pretrained("s-nlp/roberta-base-formality-ranker")
    
    @staticmethod
    def reward(prompt: str, resp: str):
        """
        Evaluates a response on 4 weighted components: format, explicability/reasoning, model strength, creativity.
        On scale from -1.0 to 1.0 (only use negatives to penalize specific behaviors)
        """
        formatting = eval_formatting(resp)
        creativity = eval_creativity(prompt, resp)
        model = eval_model(prompt, resp)
        reasoning = eval_reasoning(prompt, resp)
        
        return 0.2 * formatting + 0.15 * creativity + 0.35 * model + 0.3 * reasoning
        
    @staticmethod
    def eval_formatting(resp: str):
        """
        Scores the formatting and language of a response, based on its formality and linguistic appeal/correctness.
        """
        # 1. Formal language use
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            # For binary classification, outputs only one logit
            logits = outputs.logits

        formal_prob = torch.sigmoid(logits).item()
        # Strongly encourages formal language but overly-formal or robotic language is penalized
        formality_score = norm.pdf(formal_prob, loc=0.8, scale=1)
        
        # 2. Linguistic appeal/correctness
        