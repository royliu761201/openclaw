#!/bin/bash
#SBATCH -J LS-DYNA_TEMPLATE
#SBATCH -p dyna
#SBATCH -A jhdx
#SBATCH -N 1
#SBATCH -n 32
#SBATCH -t 24:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

# 1. Load Environment
module load lsdyna/r16.1.1

echo "========================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Running on node: $(hostname)"
echo "Start time: $(date)"
echo "========================================"

# 2. Define Input and Binary
# Standard binary for MPP execution
DYNA_BIN="mpp-dyna"
INPUT_FILE="your_input.k"

# 3. Execution (Example)
# srun $DYNA_BIN i=$INPUT_FILE ncpu=$SLURM_NTASKS
# Or simply
# $DYNA_BIN i=$INPUT_FILE ncpu=$SLURM_NTASKS memory=100m

echo "========================================"
echo "End time: $(date)"
