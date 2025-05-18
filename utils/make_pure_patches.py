import os
import numpy as np
import tifffile
from tifffile import imwrite
import concurrent.futures
import xml.etree.ElementTree as ET

def extract_roi_patches(image_path, mask_path, patch_size=(256, 256), output_dir='./Patches', label='inflammatory-cells'):
    import math

    # Open the image and the mask using tifffile with memory mapping (lazy loading)
    with tifffile.TiffFile(image_path) as img_tif, tifffile.TiffFile(mask_path) as mask_tif:
        image_series = img_tif.series[0]
        mask_series = mask_tif.series[0]

        image_shape = image_series.shape
        mask_shape = mask_series.shape

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Memory map the image and mask (so they don't load completely into memory)
        image = image_series.asarray(out='memmap')  # This is done lazily
        mask = mask_series.asarray(out='memmap')  # This is done lazily

        # Generate ROI indices (non-zero values in the mask)
        roi_indices = np.argwhere(mask > 0)  # Find non-zero mask values (ROI)

        # Define patch stride (step size)
        stride = patch_size[0]  # Adjust stride to control overlap, e.g., no overlap

        patch_data = {}  # To store patch info for XML later
        processed_patches = set()  # To track processed patches (coordinates as tuples)

        patch_index = 0  # Start with index 0 for patch naming
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []

            for y, x in roi_indices:
                # Align patch center to the stride grid
                y_start = math.floor(y / stride) * stride
                x_start = math.floor(x / stride) * stride
                y_end = y_start + patch_size[0]
                x_end = x_start + patch_size[1]

                # Ensure the patch is within the bounds of the image
                if y_end > image_shape[0] or x_end > image_shape[1]:
                    continue  # Skip patches that would exceed image boundaries

                # Define unique patch coordinates
                patch_coords = (y_start, x_start, y_end, x_end)

                # Check if the patch coordinates have already been processed
                if patch_coords not in processed_patches:
                    processed_patches.add(patch_coords)
                    patch_name = f"{os.path.basename(image_path)[:10]}{label}_{patch_index}.png"  # Custom patch naming format
                    futures.append(executor.submit(save_patch, image, y_start, x_start, y_end, x_end, patch_name))
                    patch_data[patch_name] = patch_coords
                    patch_index += 1  # Increment the patch index for each patch

            # Wait for all patches to be saved
            for future in futures:
                future.result()

    return patch_data

# Save patch function remains unchanged



# Function to save a patch
def save_patch(image, y_start, x_start, y_end, x_end, patch_name, output_dir='./Patches'):
    patch = image[y_start:y_end, x_start:x_end]
    patch_path = os.path.join(output_dir, patch_name)
    imwrite(patch_path, patch)
    print(f"Saved patch: {patch_name}")


# Paths to input and output directories
image_name = '/input/images/kidney-transplant-biopsy-wsi-pas/'
image_path = os.path.join(image_name, os.listdir(image_name)[0])
mask_name = '/input/images/tissue-mask/'
mask_path = os.path.join(mask_name, os.listdir(mask_name)[0])
output_dir = './Patches'

# Extract patches based on ROI (mask)
patch_data = extract_roi_patches(image_path, mask_path, patch_size=(1024, 1024), output_dir=output_dir, label='inflammatory-cells')


# Function to generate XML file for annotations
def create_combined_xml(patch_data, output_file):
    import xml.etree.ElementTree as ET

    root = ET.Element("ASAP_Annotations")
    annotations = ET.SubElement(root, "Annotations")

    # Add all patches and their centers as annotations
    for patch_index, (patch_name, patch_coords) in enumerate(patch_data.items()):
        y_start, x_start, y_end, x_end = patch_coords

        # Calculate the center of the patch
        center_x = (x_start + x_end) / 2
        center_y = (y_start + y_end) / 2

        # Add Center annotation
        annotation = ET.SubElement(annotations, "Annotation", {
            "Name": f"Center_{patch_index}",
            "Type": "Dot",
            "PartOfGroup": "None",
            "Color": "255, 0, 0"
        })
        coords = ET.SubElement(annotation, "Coordinates")
        ET.SubElement(coords, "Coordinate", {"X": str(center_x), "Y": str(center_y)})

        # Add Patch annotation
        annotation = ET.SubElement(annotations, "Annotation", {
            "Name": f"Patch_{patch_index}",
            "Type": "Rectangle",
            "PartOfGroup": "None",
            "Color": "255, 0, 0"
        })
        coords = ET.SubElement(annotation, "Coordinates")
        ET.SubElement(coords, "Coordinate", {"Order": "0", "X": str(x_start), "Y": str(y_start)})
        ET.SubElement(coords, "Coordinate", {"Order": "1", "X": str(x_end), "Y": str(y_start)})
        ET.SubElement(coords, "Coordinate", {"Order": "2", "X": str(x_end), "Y": str(y_end)})
        ET.SubElement(coords, "Coordinate", {"Order": "3", "X": str(x_start), "Y": str(y_end)})

    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Combined XML saved to {output_file}")



# Generate XML for the patches


xml_name = f"{os.path.basename(image_path)[:10]}inflammatory-cells.xml"
print(f"{xml_name}")
#if output_dir and not os.path.exists(output_dir):
#        os.makedirs(output_dir)
create_combined_xml(patch_data, xml_name)
