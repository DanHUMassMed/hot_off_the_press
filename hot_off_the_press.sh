#!/bin/bash
export PATH=/home/dan/miniconda3/bin:/home/dan/bin:/usr/local/bin:/usr/bin:/bin:$PATH

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate dan-dev-ml


# Run the Python script
post_new_articles_to_slack.py
status=$?

# Log success or failure to syslog
if [ $status -eq 0 ]; then
    logger "post_new_articles_to_slack: ran without errors"
else
    logger "post_new_articles_to_slack: failed with status $status"
fi