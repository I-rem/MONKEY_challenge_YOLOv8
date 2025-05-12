import os
import numpy as np
import tifffile
from tifffile import imwrite
import concurrent.futures
import xml.etree.ElementTree as ET
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def extract_roi_patches(image_path, mask_path, patch_size=(1024, 1024), output_dir='patches', label='inflammatory-cells'):
    os.makedirs(output_dir, exist_ok=True)

    # Load image and mask
    image = Image.open(image_path)
    mask = Image.open(mask_path)

    # Convert to numpy arrays
    image_np = np.array(image)
    mask_np = np.array(mask)

    h, w = mask_np.shape[:2]
    ph, pw = patch_size

    patch_id = 0
    saved_patches = []

    for y in range(0, h - ph + 1, ph):
        for x in range(0, w - pw + 1, pw):
            mask_patch = mask_np[y:y+ph, x:x+pw]
            if np.any(mask_patch > 0):
                img_patch = image_np[y:y+ph, x:x+pw]
                patch_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_{label}_{patch_id}.png"
                Image.fromarray(img_patch).save(os.path.join(output_dir, patch_filename))
                saved_patches.append(patch_filename)
                patch_id += 1

    print(f"Saved {len(saved_patches)} patches to {output_dir}")
    return saved_patches
    
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
