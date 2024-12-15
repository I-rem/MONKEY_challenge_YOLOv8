import os
import numpy as np
from tifffile import TiffFile, imwrite
import xml.etree.ElementTree as ET

def create_combined_xml(tiff_name, patch_data, output_file):
    """
    Creates a single XML file containing information for all patches, their centers, and ROI polygons.
    """
    root = ET.Element("ASAP_Annotations")
    annotations = ET.SubElement(root, "Annotations")

    # Add all patches and their centers as annotations
    for patch_index, (patch_name, patch_coords) in enumerate(patch_data.items()):
        # Add Center annotation
        center_x = (patch_coords[0][0] + patch_coords[2][0]) / 2
        center_y = (patch_coords[0][1] + patch_coords[2][1]) / 2
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
        for i, (x, y) in enumerate(patch_coords):
            ET.SubElement(coords, "Coordinate", {"Order": str(i), "X": str(x), "Y": str(y)})

    # Write to XML file
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Combined XML saved to {output_file}")

def generate_patches_from_mask_and_image(image_path, mask_path, output_dir, patch_size=1024, chunk_size=2048):
    os.makedirs(output_dir, exist_ok=True)

    with TiffFile(image_path) as tif_image, TiffFile(mask_path) as tif_mask:
        image_pages = tif_image.pages
        mask_pages = tif_mask.pages

        patch_index = 0
        patch_data = {}

        for page_idx, (image_page, mask_page) in enumerate(zip(image_pages, mask_pages)):
            print(f"Processing page {page_idx + 1}/{len(image_pages)}")

            image_shape = image_page.shape

            for y in range(0, image_shape[0], chunk_size):
                for x in range(0, image_shape[1], chunk_size):
                    # Read a chunk of the image and mask
                    image_chunk = image_page.asarray()[y:y+chunk_size, x:x+chunk_size]
                    mask_chunk = mask_page.asarray()[y:y+chunk_size, x:x+chunk_size]

                    if np.any(mask_chunk):  # Process only chunks with non-zero mask values
                        for yy in range(0, image_chunk.shape[0], patch_size):
                            for xx in range(0, image_chunk.shape[1], patch_size):
                                # Extract smaller patches from the chunk
                                patch_mask = mask_chunk[yy:yy+patch_size, xx:xx+patch_size]
                                patch_image = image_chunk[yy:yy+patch_size, xx:xx+patch_size]

                                if np.any(patch_mask):
                                    # Save the patch
                                    patch_name = f"{os.path.splitext(os.path.basename(image_path))[0]}_patch_{patch_index}"
                                    patch_output_path = os.path.join(output_dir, f"{patch_name}.png")

                                    try:
                                        imwrite(patch_output_path, patch_image)
                                        print(f"Saved patch: {patch_output_path}")
                                    except Exception as e:
                                        print(f"Failed to save patch: {patch_output_path}, error: {e}")
                                        continue

                                    # Store patch data for XML
                                    global_x = x + xx
                                    global_y = y + yy
                                    patch_coords = [
                                        (global_x, global_y),
                                        (global_x + patch_size, global_y),
                                        (global_x + patch_size, global_y + patch_size),
                                        (global_x, global_y + patch_size),
                                    ]
                                    patch_data[patch_name] = patch_coords

                                    patch_index += 1

        # Create a single combined XML for this TIFF
        xml_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_annotations.xml")
        create_combined_xml(image_path, patch_data, xml_output_path)

# Example usage
image_path = r'/input/images/kidney-transplant-biopsy-wsi-pas/sample_image.tif'
mask_path = r'/input/images/tissue-mask/sample_mask.tif'
output_dir = "./Patches"

# Generate patches
generate_patches_from_mask_and_image(image_path, mask_path, output_dir)
