#! /bin/bash

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=0:30:00
#SBATCH --mem=1GB
#SBATCH --job-name=BSH_MCP
#SBATCH --output=BSH_MCP_%A_%a.out

SCRIPT_DIR=$(scontrol show job $SLURM_JOBID | awk -F= '/Command=/{print $2}')
SCRIPT_DIR=($SCRIPT_DIR)
SCRIPT_DIR=$(dirname ${SCRIPT_DIR[0]})

INPUT_DIR=$1
OUT_DIR=$2
echo INPUT_DIR: $INPUT_DIR
echo OUT_DIR: $OUT_DIR

mkdir $OUT_DIR

for IMAGE in $INPUT_DIR/*; do
    IMAGE_NAME=${IMAGE##*/}

    echo sbatch $SCRIPT_DIR/hrpqct_mask.sh $IMAGE $OUT_DIR/$IMAGE_NAME
    sbatch $SCRIPT_DIR/hrpqct_mask.sh $IMAGE $OUT_DIR/$IMAGE_NAME

done