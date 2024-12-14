import os
import xml.etree.ElementTree as ET
from tifffile import TiffFile, imwrite
import numpy as np

#def create_combined_xml(tiff_name, patch_data, roi_coordinates, output_file):
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

    # Add ROI annotations 
    '''
    for roi_index, roi_coords in enumerate(roi_coordinates):
        annotation = ET.SubElement(annotations, "Annotation", {
            "Name": f"ROI_{roi_index}",
            "Type": "Polygon",
            "PartOfGroup": "None",
            "Color": "#73d216"
        })
        coords = ET.SubElement(annotation, "Coordinates")
        for i, (x, y) in enumerate(roi_coords):
            ET.SubElement(coords, "Coordinate", {"Order": str(i), "X": str(x), "Y": str(y)})
   '''
    # Write to XML file
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Combined XML saved to {output_file}")



def parse_rois_from_mask(mask, tile_size=2048):
    from skimage.measure import label, regionprops
    roi_polygons = []

    for y in range(0, mask.shape[0], tile_size):
        for x in range(0, mask.shape[1], tile_size):
            mask_tile = mask[y:y+tile_size, x:x+tile_size]
            if np.any(mask_tile):  # Only process non-empty tiles
                labeled_tile = label(mask_tile > 0, connectivity=1).astype(np.int32)
                props = regionprops(labeled_tile)

                for prop in props:
                    coords = prop.coords + [y, x]  # Adjust coordinates to global position
                    polygon = [(c[1], c[0]) for c in coords]
                    roi_polygons.append(polygon)

    return roi_polygons



def generate_patches_from_mask_and_image(image_path, mask_path, output_dir, patch_size=1024):
    os.makedirs(output_dir, exist_ok=True)

    # Read the mask and image
    with TiffFile(image_path) as tif_image, TiffFile(mask_path) as tif_mask:
        image = tif_image.asarray()
        mask = tif_mask.asarray()

   # if image.shape != mask.shape:
   #     raise ValueError("Image and mask dimensions do not match.")

    print(f"Processing {image_path} with {mask_path}")
    print(f"Image shape: {image.shape}, Mask shape: {mask.shape}")

    patch_index = 0
    patch_data = {}

    # Parse ROIs from the mask
    #roi_coordinates = parse_rois_from_mask(mask)
    #print(f"Parsed {len(roi_coordinates)} ROIs from the mask.")

    # Iterate through the mask to find non-zero regions
    for y in range(0, mask.shape[0], patch_size):
        for x in range(0, mask.shape[1], patch_size):
            # Check if the current patch area in the mask has any non-zero values
            mask_patch = mask[y:y+patch_size, x:x+patch_size]
            if np.any(mask_patch):
                # Extract the corresponding image patch
                image_patch = image[y:y+patch_size, x:x+patch_size]

                # Save patch
                patch_name = f"{os.path.splitext(os.path.basename(image_path))[0][0:10]}inflammatory-cells_{patch_index}"
                patch_output_path = os.path.join(output_dir, f"{patch_name}.png")
                try:
                    imwrite(patch_output_path, image_patch)
                    print(f"Saved patch: {patch_output_path}")
                except Exception as e:
                    print(f"Failed to save patch: {patch_output_path}, error: {e}")
                    continue

                # Store patch data for XML
                patch_coords = [
                    (x, y),
                    (x + patch_size, y),
                    (x + patch_size, y + patch_size),
                    (x, y + patch_size),
                ]
                patch_data[patch_name] = patch_coords

                patch_index += 1

    # Create a single combined XML for this TIFF
    xml_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0][0:10]}inflammatory-cells.xml")
    #create_combined_xml(image_path, patch_data, roi_coordinates, xml_output_path)
    create_combined_xml(image_path, patch_data, xml_output_path)


image_path = r'./input/images/kidney-transplant-biopsy-wsi-pas/.'
image_name = "./input/images/kidney-transplant-biopsy-wsi-pas/" + os.listdir(image_path)[0]
mask_path = r'./input/images/tissue-mask/.'
mask_name = "./input/images/tissue-mask/" + os.listdir(mask_path)[0]
# output_dir = "S:/GrandChallenge/Monkey/Dataset2/pure_patches/patches"
output_dir = "./Patches"
generate_patches_from_mask_and_image(image_name, mask_name, output_dir)
