import os
import json
from datasets import Dataset, DatasetDict
from transformers import Trainer
from qlora import LlmQLoRA
from ppo import LlmPPO 

class DataLoader:
    # Structure of JSON: problem statement, solution, citations
    @staticmethod
    def load_json(json_path: str):
        required_keys = {'problem', 'solution', 'metadata'}
        with open(json_path, 'r') as file:
            raw_data = json.load(file)

        # Ensure each dict has required keys
        for i, item in enumerate(raw_data):
            keys_lower = {k.lower() for k in item.keys()}
            if not required_keys.issubset(keys_lower):
                raise Exception(f"Entry {i} missing required keys")

        # Normalize keys to expected names and keep only needed keys
        filtered_data = []
        for item in raw_data:
            # Map keys ignoring case
            keys_map = {k.lower(): k for k in item.keys()}
            filtered_data.append({
                "problem": item[keys_map.get("problem")],
                "solution": item[keys_map.get("solution")],
                "metadata": item[keys_map.get("metadata")],
            })

        return filtered_data

if __name__ == "__main__":
    json_path = "mathModelingLLM/sciteProcessing/jsons/processed_papers_with_chatgpt.json" 
    output_dir = "./qlora-finetuned"
    model_name = "mistralai/Mistral-7B-Instruct-v0.1"

    # Load and preprocess data
    data = DataLoader.load_json(json_path)
    llm = LlmQLoRA(model=model_name, model_name="Mistral7B")

    # Format prompts with problem and solution into instruction/response style text
    formatted_samples = llm.format_prompts(data)
    dataset = Dataset.from_list(formatted_samples)

    # Simple train/eval split
    split = dataset.train_test_split(test_size=0.1)
    train_dataset = split['train']
    eval_dataset = split['test']

    # Fine tune with Lora
    llm.make_peft_model_qlora()
    llm.train_peft(
        training_dir=output_dir,
        output_dir=output_dir,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset
    )

    # Save fine-tuned model
    llm.peft_model.save_pretrained(output_dir)
    llm.tokenizer.save_pretrained(output_dir)
    print(f"Fine-tuned model saved to {output_dir}")
