#! /bin/bash

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --mem=5GB
#SBATCH --job-name=SH_MCP
#SBATCH --output=SH_MCP_%A_%a.out

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=8
SCRIPT_DIR=$(scontrol show job $SLURM_JOBID | awk -F= '/Command=/{print $2}')
SCRIPT_DIR=($SCRIPT_DIR)
SCRIPT_DIR=$(dirname ${SCRIPT_DIR[0]})

INPUT_IMAGE=$1
OUT_IMAGE=$2

echo python $SCRIPT_DIR/autocontour.py $INPUT_IMAGE $OUT_IMAGE
python $SCRIPT_DIR/autocontour.py $INPUT_IMAGE $OUT_IMAGE