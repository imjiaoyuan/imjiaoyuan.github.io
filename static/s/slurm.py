#!/usr/bin/env python3
import os, glob, sys
from subprocess import call

INPUT_DIR = "input"
FILE_PATTERN = "*.fq.gz"
OUTPUT_DIR = "output"
COMMAND_TEMPLATE = "${INPUT_DIR}/${FILEID}.fq.gz --outdir ${OUTPUT_DIR} --threads ${SLURM_CPUS} --mem ${SLURM_MEM}G"

JOB_DIR = "./jobs"
LOG_DIR = "./logs"
SLURM_PARTITION = "compute1,compute2"
SLURM_CPUS = "10"
SLURM_MEM = "100"
CONDA_ENV = "omics"

def gen_commands():
    with open("commands.txt", "w") as f:
        for sample_file in glob.glob(os.path.join(INPUT_DIR, FILE_PATTERN)):
            fileid = os.path.basename(sample_file).split('.')[0]
            cmd = COMMAND_TEMPLATE.replace("${INPUT_DIR}", INPUT_DIR)
            cmd = cmd.replace("${FILEID}", fileid)
            cmd = cmd.replace("${OUTPUT_DIR}", OUTPUT_DIR)
            f.write(cmd + "\n")

def build_jobs():
    os.makedirs(JOB_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    lines = open("commands.txt", "r").readlines()
    for sample_file in glob.glob(os.path.join(INPUT_DIR, FILE_PATTERN)):
        fileid = os.path.basename(sample_file).split('.')[0]
        job_file = os.path.join(JOB_DIR, f"{fileid}.sl")
        log_prefix = os.path.join(LOG_DIR, f"{fileid}")
        with open(job_file, "w") as f:
            f.write("#!/bin/sh\n")
            f.write(f"#SBATCH -p {SLURM_PARTITION}\n")
            f.write(f"#SBATCH -n 1 -c {SLURM_CPUS} --mem={SLURM_MEM}g\n")
            f.write(f"#SBATCH -o {log_prefix}.out\n")
            f.write(f"#SBATCH -e {log_prefix}.err\n")
            f.write(f"#SBATCH -D {os.getcwd()}\n\n")
            f.write("source ~/miniconda3/etc/profile.d/conda.sh\n")
            f.write(f"conda activate {CONDA_ENV}\n\n")
            cmd = COMMAND_TEMPLATE.replace("${INPUT_DIR}", INPUT_DIR)
            cmd = cmd.replace("${FILEID}", fileid)
            cmd = cmd.replace("${OUTPUT_DIR}", OUTPUT_DIR)
            f.write(cmd + "\n")

def submit_jobs():
    for job_file in glob.glob(os.path.join(JOB_DIR, "*.sl")):
        call(["sbatch", job_file])

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit("Usage: python3 script.py [gen_commands|build_jobs|submit_jobs]")
    cmd = {"gen_commands": gen_commands, "build_jobs": build_jobs, "submit_jobs": submit_jobs}
    cmd.get(sys.argv[1], lambda: sys.exit("Invalid command"))()