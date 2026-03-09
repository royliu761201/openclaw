#!/bin/bash

# Configuration
MODEL_PATH="/jhdx0003008/models/Qwen2.5-14B-Instruct"
OUTPUT_DIR="experiments/results/medtime_swift_v1"
TRAIN_DATASET="data/swift/syn_train.jsonl"
VAL_DATASET="data/swift/syn_dev.jsonl"

# Use all 5 GPUs
export CUDA_VISIBLE_DEVICES=0,1,2,3,4

# Launch SWIFT SFT
# We use deepspeed zero3 for efficient 14B distribution
/root/miniconda3/envs/ai4s_env/bin/python -m swift.cli.sft \
    --model_type qwen2_5-14b-instruct \
    --model_id_or_path $MODEL_PATH \
    --sft_type lora \
    --dataset $TRAIN_DATASET \
    --val_dataset $VAL_DATASET \
    --learning_rate 2e-4 \
    --batch_size 1 \
    --eval_steps 20 \
    --save_steps 20 \
    --max_steps 100 \
    --gradient_accumulation_steps 16 \
    --output_dir $OUTPUT_DIR \
    --deepspeed default-zero3 \
    --lora_target_modules ALL \
    --self_cognition_sample 0 \
    --dtype bfloat16
