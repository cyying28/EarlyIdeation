import os
import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    pipeline
)
from datasets import Dataset
from dotenv import load_dotenv

class LlmQLoRA:
    """
    Quantized (less memory) version of LoRA (Low-Rank Adaptation of Large Language Models).
    Introduces trainable rank decomposition matrices into each layer of the transformer,
    so it alters the matrix rather than the pre-trained weights. In inference, it uses these
    matrices in tandem with the pre-trained weights to produce output.
    """
    def __init__(self, model: str, model_name: str):
        self.use_cuda = torch.cuda.is_available()
        self.device_map = "auto" if self.use_cuda else "cpu"
        self.device = 0 if self.use_cuda else -1
        self.model_name = model_name
        load_dotenv()
        self.auth_token = os.getenv("HF_AUTH_TOKEN")

        compute_dtype = torch.float16 if self.use_cuda else torch.float32

        self.bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=False,
        ) if self.use_cuda else None

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model,
            device_map=self.device_map,
            quantization_config=self.bnb_config,
            trust_remote_code=True,
            use_auth_token=True,
            token=auth_token
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model,
            trust_remote_code=True,
            padding_side="left",
            use_fast=False,
            token=auth_token
        )

        # Set BOS and EOS tokens manually
        self.tokenizer.add_eos_token = True
        self.tokenizer.add_bos_token = True

        self.peft_model = None
        self.peft_trainer = None

    def format_prompts(self, samples: list[dict]):
        """
        Format fields of sample ('instruction', 'output') and format them as string.
        Adds to the sample 
        """
        
        INTRO_BLURB = "Below is an instruction that describes a task. Write a response that appropriately completes the request."
        INSTRUCTION_KEY = "### Instruct: Generate a math modeling solution for the below question."
        RESPONSE_KEY = "### Output:"
        END_KEY = "### End"

        for sample in samples:
            input_context = f"{sample['problem']}" if sample["problem"] else None
            response = f"{RESPONSE_KEY}\n{sample['solution']}"
            parts = [INTRO_BLURB, INSTRUCTION_KEY, input_context, response, END_KEY]
            sample["instruction"] = "\n\n".join(part for part in parts if part)

        return samples

    def prompt_llm(self, text: str):
        model_for_inference = self.peft_model if self.peft_model is not None else self.model

        generator = pipeline(
            "text-generation",
            model=model_for_inference,
            tokenizer=self.tokenizer,
            device=self.device
        )
        outputs = generator(text, do_sample=True, top_p=0.95, temperature=0.7)
        return outputs[0]['generated_text']

    def make_peft_model_qlora(self):
        """
        Make PEFT model to fine tune a small subset of weights
        """
        if self.use_cuda:
            self.model = prepare_model_for_kbit_training(self.model)
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "dense"],
            bias="none",
            lora_dropout=0.05,
            task_type="CAUSAL_LM"
        )
        self.peft_model = get_peft_model(self.model, lora_config)
        print("Successfully added peft_model")

    def train_peft(self, training_dir, output_dir, train_dataset, eval_dataset):
        """
        Train the PEFT model on the training data and output to directory
        """
        peft_training_args = TrainingArguments(
            output_dir=output_dir,
            warmup_steps=1,
            num_train_epochs=3,
            logging_dir=os.path.join(training_dir, "logs"),
            save_strategy="epoch",
            fp16=self.use_cuda,
            evaluation_strategy="epoch",
            do_eval=True,
            report_to="none"
        )

        self.peft_model.config.use_cache = False
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

        self.peft_trainer = Trainer(
            model=self.peft_model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            args=peft_training_args,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )

        self.peft_trainer.train()
        self.peft_model.save_pretrained(training_dir)
        print(f"Finished fine-tuning {self.model_name}")

    def get_inference_model(self):
        model_for_inference = self.peft_model if self.peft_model is not None else self.model
        return pipeline(
            "text-generation",
            model=model_for_inference,
            tokenizer=self.tokenizer,
            device=self.device
        )

    def load_peft_model(self, base_model_path: str, peft_model_path: str):
        """
        Load the base model and overlay the LoRA PEFT adapter
        """
        # Reload base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map=self.device_map,
            quantization_config=self.bnb_config,
            trust_remote_code=True,
            use_auth_token=True
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_path,
            trust_remote_code=True,
            padding_side="left",
            add_eos_token=True,
            add_bos_token=True,
            use_fast=False
        )

        self.peft_model = PeftModel.from_pretrained(
            self.model,
            peft_model_path,
            device_map=self.device_map
        )

        print(f"Loaded PEFT model from {peft_model_path} on base model {base_model_path}")

    def print_number_of_trainable_model_parameters(self):
        """
        Evaluate how much of the model can be fine-tuned
        """
        trainable_model_params = 0
        all_model_params = 0
        for _, param in self.peft_model.named_parameters():
            all_model_params += param.numel()
            if param.requires_grad:
                trainable_model_params += param.numel()
        percent = (trainable_model_params / all_model_params) * 100
        return (
            f"Trainable model parameters: {trainable_model_params}\n"
            f"All model parameters: {all_model_params}\n"
            f"Percentage trainable: {percent:.2f}%"
        )

# USAGE:
# llm = LlmQLoRA(model="mistralai/Mistral-7B-Instruct-v0.1", model_name="Mistral7B")
# llm.load_peft_model(
#     base_model_path="mistralai/Mistral-7B-Instruct-v0.1",
#     peft_model_path="./qlora-finetuned"
# )

# inference_pipe = llm.get_inference_model()
# print(inference_pipe("Describe a mathematical model for tumor growth.")[0]['generated_text'])
