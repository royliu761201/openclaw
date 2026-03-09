#!/bin/bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate medtime
echo "=== Installing Dependencies ==="
pip install lightning
pip install -U transformers
pip install -U peft
pip install -U accelerate
echo "=== Environment Info ==="
pip list | grep lightning
python -c "import lightning; print('Lightning OK')"
