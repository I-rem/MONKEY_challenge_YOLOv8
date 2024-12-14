import subprocess
import os

os.remove("input/images/tissue-mask/README.md")
os.remove("input/images/kidney-transplant-biopsy-wsi-pas/README.md")

python_path = "/venv/bin/python"

subprocess.run([python_path, "./utils/make_pure_patches.py"])
subprocess.run([python_path, "./utils/results_with_normalization_roi.py"])
subprocess.run([python_path, "./utils/pixel_to_mm.py"])
