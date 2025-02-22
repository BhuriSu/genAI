# model/llm/fine_tuning.py
from unsloth import FastLanguageModel
import torch
from torch.utils.data import Dataset, DataLoader
from ..config import LLMConfig

class FinancialDataset(Dataset):
    def __init__(self, data, tokenizer):
        self.data = data
        self.tokenizer = tokenizer
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        encoded = self.tokenizer(
            item["text"],
            truncation=True,
            max_length=512,
            padding="max_length",
            return_tensors="pt"
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(),
            "attention_mask": encoded["attention_mask"].squeeze(),
            "labels": encoded["input_ids"].squeeze()
        }

class LLMFineTuner:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=config.model_name,
            max_seq_length=config.max_length,
            gradient_checkpointing=config.gradient_checkpointing
        )
    
    def prepare_data(self, financial_data):
        dataset = FinancialDataset(financial_data, self.tokenizer)
        return DataLoader(dataset, batch_size=self.config.batch_size, shuffle=True)
    
    def train(self, train_dataloader):
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.config.learning_rate)
        
        for epoch in range(self.config.num_epochs):
            self.model.train()
            for batch in train_dataloader:
                optimizer.zero_grad()
                outputs = self.model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"]
                )
                loss = outputs.loss
                loss.backward()
                optimizer.step()