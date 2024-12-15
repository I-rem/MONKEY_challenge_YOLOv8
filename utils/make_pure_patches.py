import numpy as np
import os
from tifffile import TiffFile, TiffWriter
from xml.etree.ElementTree import Element, SubElement, ElementTree

def generate_patches_from_mask_and_image(image_path, mask_path, output_dir, patch_size=1024):
    os.makedirs(output_dir, exist_ok=True)

    patch_index = 0
    patch_data = {}

    # Open the mask file and get the shape
    with TiffFile(mask_path) as tif_mask:
        mask = tif_mask.pages[0].asarray()
    print(f"Mask shape: {mask.shape}")

    # Open the image file and get its shape without loading the full image into memory
    with TiffFile(image_path) as tif_image:
        image_shape = tif_image.pages[0].shape  # This only gets metadata (dimensions), no pixel data loaded
    print(f"Image shape: {image_shape}")

    # Find non-zero coordinates from the mask
    non_zero_indices = np.nonzero(mask)

    for y, x in zip(*non_zero_indices):
        # Calculate the top-left corner of the patch based on the non-zero mask coordinates
        patch_start_y = (y // patch_size) * patch_size
        patch_start_x = (x // patch_size) * patch_size

        # Calculate the bottom-right corner of the patch
        patch_end_y = patch_start_y + patch_size
        patch_end_x = patch_start_x + patch_size

        # Only process the patch if it has not been processed before
        patch_coords = ((patch_start_x, patch_start_y), (patch_end_x, patch_end_y))

        if patch_coords in patch_data:
            continue  # Skip if the patch has already been processed

        # Extract the mask patch for the current region
        mask_patch = mask[patch_start_y:patch_end_y, patch_start_x:patch_end_x]
        
        # Skip patches with no non-zero pixels in the mask (ROI)
        if np.count_nonzero(mask_patch) == 0:
            continue

        # Read the corresponding image patch from the WSI
        with TiffFile(image_path) as tif_image:
            image_patch = tif_image.pages[0].asarray()[patch_start_y:patch_end_y, patch_start_x:patch_end_x]

        # Save the image patch
        patch_name = f"{os.path.splitext(os.path.basename(image_path))[0][0:10]}inflammatory-cells_{patch_index}"
        patch_output_path = os.path.join(output_dir, f"{patch_name}.png")

        # Use TiffWriter to write the patch image to a TIFF file
        with TiffWriter(patch_output_path) as patch_tiff:
            patch_tiff.save(image_patch)

        print(f"Saved patch: {patch_output_path}")

        # Store patch coordinates for XML
        patch_data[patch_coords] = patch_name
        patch_index += 1

    # Save patch data to a combined XML file
    xml_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0][0:10]}inflammatory-cells.xml")
    create_combined_xml(image_path, patch_data, xml_output_path)

def create_combined_xml(tiff_name, patch_data, output_file):
    """
    Creates a single XML file containing information for all patches, their centers, and ROI polygons.
    """
    root = Element("ASAP_Annotations")
    annotations = SubElement(root, "Annotations")

    # Add all patches and their centers as annotations

    for patch_index, (patch_coords, patch_name) in enumerate(patch_data.items()):
        # Add Center annotation
        center_x = (patch_coords[0][0] + patch_coords[1][0]) / 2
        center_y = (patch_coords[0][1] + patch_coords[1][1]) / 2

        annotation = SubElement(annotations, "Annotation", {
            "Name": f"Center_{patch_index}",
            "Type": "Dot",
            "PartOfGroup": "None",
            "Color": "255, 0, 0"
        })
        coords = SubElement(annotation, "Coordinates")
        SubElement(coords, "Coordinate", {"X": str(center_x), "Y": str(center_y)})

        # Add Patch annotation
        annotation = SubElement(annotations, "Annotation", {
            "Name": f"Patch_{patch_index}",
            "Type": "Rectangle",
            "PartOfGroup": "None",
            "Color": "255, 0, 0"
        })
        coords = SubElement(annotation, "Coordinates")

        for i, (x, y) in enumerate([patch_coords[0], (patch_coords[0][0], patch_coords[1][1]),
                                    patch_coords[1], (patch_coords[1][0], patch_coords[0][1])]):
            SubElement(coords, "Coordinate", {"Order": str(i), "X": str(x), "Y": str(y)})

    # Write to XML file
    tree = ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Combined XML saved to {output_file}")


# Example usage
image_path = r'/input/images/kidney-transplant-biopsy-wsi-pas/.' 
image_name = "/input/images/kidney-transplant-biopsy-wsi-pas/" + os.listdir(image_path)[0]
mask_path = r'/input/images/tissue-mask/.' 

mask_name = "/input/images/tissue-mask/" + os.listdir(mask_path)[0]
output_dir = "./Patches"

# Generate patches
generate_patches_from_mask_and_image(image_name, mask_name, output_dir)
