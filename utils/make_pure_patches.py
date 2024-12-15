from tifffile import TiffFile
from PIL import Image
import numpy as np
import os
from xml.etree.ElementTree import Element, SubElement, ElementTree

Image.MAX_IMAGE_PIXELS = None

def generate_patches_from_mask_and_image(image_path, mask_path, output_dir, patch_size=1024):
    os.makedirs(output_dir, exist_ok=True)

    # Load the mask entirely into memory
    with TiffFile(mask_path) as tif_mask:
        mask = tif_mask.asarray()

    print(f"Processing image: {image_path}, mask: {mask_path}")
    print(f"Mask shape: {mask.shape}")

    patch_index = 0
    patch_data = {}

    # Get non-zero regions from the mask
    non_zero_indices = np.nonzero(mask)

    # Open the WSI image using Pillow
    wsi_image = Image.open(image_path)

    # Track processed patches
    processed_patches = set()

    for y, x in zip(*non_zero_indices):
        # Calculate the patch coordinates
        patch_start_y = (y // patch_size) * patch_size
        patch_start_x = (x // patch_size) * patch_size

        # Convert patch_coords to a tuple of tuples to make it hashable
        patch_coords = (
            (patch_start_x, patch_start_y),
            (patch_start_x + patch_size, patch_start_y),
            (patch_start_x + patch_size, patch_start_y + patch_size),
            (patch_start_x, patch_start_y + patch_size),
        )

        if patch_coords in processed_patches:
            continue  # Skip duplicate patches

        # Extract the patch using Pillow
        image_patch = wsi_image.crop((
            patch_start_x,
            patch_start_y,
            patch_start_x + patch_size,
            patch_start_y + patch_size
        ))

        # Save the image patch
        patch_name = f"{os.path.splitext(os.path.basename(image_path))[0]}_patch_{patch_index}"
        patch_output_path = os.path.join(output_dir, f"{patch_name}.png")
        image_patch.save(patch_output_path)
        print(f"Saved patch: {patch_output_path}")

        # Store patch data for XML
        patch_data[patch_name] = patch_coords
        processed_patches.add(patch_coords)  # Mark this patch as processed using a tuple of tuples
        patch_index += 1

    # Save patch data to a combined XML file
    xml_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_patches.xml")
    create_combined_xml(image_path, patch_data, xml_output_path)



def create_combined_xml(tiff_name, patch_data, output_file):
    """
    Creates a single XML file containing information for all patches, their centers, and ROI polygons.
    """
    root = Element("ASAP_Annotations")
    annotations = SubElement(root, "Annotations")

    # Add all patches and their centers as annotations
    for patch_index, (patch_name, patch_coords) in enumerate(patch_data.items()):
        # Add Center annotation
        center_x = (patch_coords[0][0] + patch_coords[2][0]) / 2
        center_y = (patch_coords[0][1] + patch_coords[2][1]) / 2
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
        for i, (x, y) in enumerate(patch_coords):
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
