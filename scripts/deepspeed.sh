#!/bin/bash

deepspeed --num_gpus=1 ../transformers/examples/pytorch/text-generation/run_generation.py \
    --deepspeed ../transformers/tests/deepspeed/ds_config_zero2.json \
    --model_type=gpt2 \
    --model_name_or_path=gpt2 \
    --per_device_train_batch_size 1 \
    --do_train \
    --max_train_samples 500 \
    --num_train_epochs 1