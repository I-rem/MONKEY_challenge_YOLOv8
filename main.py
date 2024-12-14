import subprocess
import os

if __name__ == "__main__":
    python_path = "/venv/bin/python"

    subprocess.run([python_path, "/utils/make_pure_patches.py"])
    subprocess.run([python_path, "/utils/results_with_normalization_roi.py"])
    subprocess.run([python_path, "/utils/pixel_to_mm.py"])
