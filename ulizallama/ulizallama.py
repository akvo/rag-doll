#  XXXX !pip install -q  sentencepiece accelerate==0.21.0 peft==0.4.0 bitsandbytes==0.40.2 transformers==4.31.0 trl==0.4.7 tensorboard
#  XXXX import os, torch, logging
#  XXXX import pandas as pd
#  XXXX from datasets import load_dataset, Dataset
#  XXXX from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaTokenizer, LlamaForCausalLM,BitsAndBytesConfig, HfArgumentParser, TrainingArguments, pipeline
#  XXXX from peft import LoraConfig, PeftModel
#  XXXX from trl import SFTTrainer

import torch
from transformers import AutoTokenizer, GenerationConfig, AutoModelForCausalLM, BitsAndBytesConfig

# XXX review for necessiry...
# from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaTokenizer, LlamaForCausalLM,BitsAndBytesConfig, HfArgumentParser, TrainingArguments, pipeline


# --- Model and Initialization ---

# XXX Review for necessity...

# Model and tokenizer names
base_model_name = "Jacaranda/UlizaLlama"

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
# XXX tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"  # Fix for fp16

# Quantization Config
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=False
)

# Model
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    # quantization_config=quant_config,
    device_map={"": 0},
    low_cpu_mem_usage=True,
    # from_tf=True,
)
base_model.config.use_cache = False
base_model.config.pretraining_tp = 1

# --- Inference ---


q1 = "Naweza Kununua Bima ya Afya Nikitanguliwa na Hali Iliyopo Tayari?"
q2 = "Can I Buy Health Insurance With A Pre-Existing Condition?"
test_strings =[q1, q2]
predictions = []
for test in test_strings:
    prompt = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

    ### Instruction:
    {}

    ### Response:""".format(test)
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to('cuda')

    # XXX generation_output = peft_model.generate(
    generation_output = base_model.generate(
        input_ids=input_ids,
        generation_config=GenerationConfig(do_sample=True,temp=0.2,top_p= 0.75,num_beams=1),
        max_new_tokens=256,

    )
    predictions.append(tokenizer.decode(generation_output[0]))


def extract_response_text(input_string):
    start_marker = '### Response:'
    end_marker = '###'

    start_index = input_string.find(start_marker)
    if start_index == -1:
        return None

    start_index += len(start_marker)

    end_index = input_string.find(end_marker, start_index)
    if end_index == -1:
        return input_string[start_index:]

    return input_string[start_index:end_index].strip()

for i in range(2):
    pred = predictions[i]
    text = test_strings[i]
    print("Question: "+text+'\n')
    print("Generated Response: " +extract_response_text(pred))
    print('--------')

