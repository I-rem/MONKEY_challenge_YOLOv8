import os

os.system("python ./utils/make_pure_patches.py")  
os.system("python ./utils/results_with_normalization_roi.py")  
os.system("python ./utils/pixel_to_mm.py")  

os.remove("detected-inflammatory-cells.json")
os.remove("detected-lymphocytes.json")
os.remove("detected-monocytes.json")
