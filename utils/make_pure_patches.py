from tifffile import TiffFile, imwrite
import os
import numpy as np
import xml.etree.ElementTree as ET


def create_combined_xml(tiff_name, patch_data, output_file):
    """
    Creates a single XML file containing information for all patches and their centers.
    """
    root = ET.Element("ASAP_Annotations")
    annotations = ET.SubElement(root, "Annotations")

    for patch_index, (patch_name, patch_coords) in enumerate(patch_data.items()):
        # Add Center annotation
        center_x = (patch_coords[0][0] + patch_coords[2][0]) / 2
	@@ -40,67 +40,62 @@ def create_combined_xml(tiff_name, patch_data, output_file):
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Combined XML saved to {output_file}")


def generate_patches_from_mask_and_image(image_path, mask_path, output_dir, patch_size=1024):
    os.makedirs(output_dir, exist_ok=True)

    # Open the TIFF files
    with TiffFile(image_path) as tif_image, TiffFile(mask_path) as tif_mask:
        # Get the TIFF pages for memory-efficient access
        image_page = tif_image.pages[0]
        mask_page = tif_mask.pages[0]

        image_shape = image_page.shape
        mask_shape = mask_page.shape

        print(f"Processing {image_path} with {mask_path}")
        print(f"Image shape: {image_shape}, Mask shape: {mask_shape}")

        patch_index = 0
        patch_data = {}

        # Iterate over the mask in chunks to extract patches
        for y in range(0, mask_shape[0], patch_size):
            for x in range(0, mask_shape[1], patch_size):
                # Extract the patch from the mask
                mask_patch = mask_page.asarray()[y:y + patch_size, x:x + patch_size]
                if np.any(mask_patch):  # Process only non-empty patches
                    # Extract the corresponding image patch
                    image_patch = image_page.asarray()[y:y + patch_size, x:x + patch_size]

                    # Save the patch
                    patch_name = f"{os.path.splitext(os.path.basename(image_path))[0][0:10]}_patch_{patch_index}"
                    patch_output_path = os.path.join(output_dir, f"{patch_name}.png")
                    imwrite(patch_output_path, image_patch)

                    # Store patch data for XML
                    patch_coords = [
                        (x, y),
                        (x + patch_size, y),
                        (x + patch_size, y + patch_size),
                        (x, y + patch_size),
                    ]
                    patch_data[patch_name] = patch_coords

                    patch_index += 1

        # Save combined XML
        xml_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_annotations.xml")
        create_combined_xml(image_path, patch_data, xml_output_path)


# Example usage
image_path = r'/input/images/kidney-transplant-biopsy-wsi-pas/.' 
image_name = "/input/images/kidney-transplant-biopsy-wsi-pas/" + os.listdir(image_path)[0]
mask_path = r'/input/images/tissue-mask/.' 

mask_name = "/input/images/tissue-mask/" + os.listdir(mask_path)[0]
output_dir = "./Patches"

# Generate patches
generate_patches_from_mask_and_image(image_name, mask_name, output_dir)
