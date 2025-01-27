#!/bin/sh


experiment=$1
dir=$2
oak_dir=$3

reference_fasta=/scratch/groups/akundaje/anusri/chromatin_atlas/reference/hg38.genome.fa
singularity exec --nv /home/groups/akundaje/anusri/simg/tf-atlas_gcp-modeling.sif nvidia-smi
#singularity exec --nv /home/groups/akundaje/anusri/simg/tf-atlas_gcp-modeling.sif bash interpret_counts.sh $reference_fasta $dir/preprocessing/downloads/peaks_no_blacklist.bed.gz $dir/interpret_counts_full/$experiment $dir/chrombpnet_model/chrombpnet_wo_bias.h5
singularity exec --nv /home/groups/akundaje/anusri/simg/tf-atlas_gcp-modeling.sif bash interpret_counts.sh $reference_fasta $dir/preprocessing/downloads/30K.ranked.subsample.overlap.bed $dir/interpret_counts_full/$experiment $dir/chrombpnet_model/chrombpnet_wo_bias.h5
wait
cp -r $dir/interpret_counts_full $oak_dir


