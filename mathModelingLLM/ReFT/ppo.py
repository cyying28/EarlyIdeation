import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    pipeline)
from datasets import load_dataset
from trl import PPOTrainer, PPOConfig
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as import pd
import numpy as np

class LlmPPO:
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        # Expects a fine-tuned LLM
        self.model = AutoModelForCausalLMWithValueHead.from_pretrained(model_path).to("cuda")
        self.config = PPOConfig(
            # Want less memory use (otherwise use batch = 2)
            batch_size=1,
            # Smaller for less memory use
            forward_batch_size=1,
            learning_rate=1.41e-5,
            log_with=None,
            # Should usually be ≤ batch size
            mini_batch_size=1,
            ppo_epochs=4
        )
        self.trainer = PPOTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            config=self.config
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def train(self, prompts):
        for prompt in prompts:
            tokenized = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            generation = self.model.generate(**tokenized, max_new_tokens=100)
            response_text = self.tokenizer.decode(generation[0], skip_special_tokens=True)
            reward = self.reward_fn(response_text)

            print("Prompt:", prompt)
            print("Response:", response_text)
            print("Reward:", reward)

            self.trainer.step([prompt], [response_text], [reward])

        self.trainer.save_pretrained("./ppo-optimized-mathmodel")
        print("PPO-optimized model saved to ./ppo-optimized-mathmodel")

    def get_inference_model(self):
        return pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)
    
# Usage
# ppo = PPOReinforcer()
# prompts = [
#     "Describe a mathematical model for simulating tumor growth.",
#     "Write Python code to solve a diffusion equation."
# ]
# ppo.train(prompts)

# Evaluate PPO model
# inference_pipe = ppo.get_inference_model()
# print(inference_pipe("Write a model for fluid flow.")[0]['generated_text'])