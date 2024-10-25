#!/bin/bash

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate dan-dev-ml

# Run the Python script
post_new_articles_to_slack.py