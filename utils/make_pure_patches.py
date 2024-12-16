import os
import xml.etree.ElementTree as ET
from tifffile import TiffFile, imwrite
import numpy as np
import zarr
import tifffile

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



def tiff_to_zarr(tiff_path, zarr_path, chunk_size=(1024, 1024)):
    """
    Converts a TIFF image to Zarr format with specified chunk size.
    """
    with tifffile.TiffFile(tiff_path) as tif:
        image = tif.asarray()
        
        zarr_array = zarr.open(
            zarr_path,
            mode='w',
            shape=image.shape,
            chunks=chunk_size,
            dtype=image.dtype
        )
        zarr_array[:] = image
    
    print(f"Converted {tiff_path} to Zarr format at {zarr_path}")

def generate_patches_from_zarr(image_zarr_path, mask_zarr_path, output_dir, patch_size=1024):
    """
    Generates patches from Zarr files (image and mask).
    """
    os.makedirs(output_dir, exist_ok=True)

    image = zarr.open(image_zarr_path, mode='r')
    mask = zarr.open(mask_zarr_path, mode='r')

    #if image.shape != mask.shape:
     #   raise ValueError("Image and mask dimensions do not match.")

    print(f"Processing {image_zarr_path} with {mask_zarr_path}")
    print(f"Image shape: {image.shape}, Mask shape: {mask.shape}")

    patch_index = 0
    patch_data = {}

    for y in range(0, mask.shape[0], patch_size):
        for x in range(0, mask.shape[1], patch_size):
            mask_patch = mask[y:y+patch_size, x:x+patch_size]
            if np.any(mask_patch):
                image_patch = image[y:y+patch_size, x:x+patch_size]

                patch_name = f"{os.path.basename(image_zarr_path)[:10]}inflammatory-cells_{patch_index}"
                patch_output_path = os.path.join(output_dir, f"{patch_name}.png")
                try:
                    imwrite(patch_output_path, image_patch)
                    print(f"Saved patch: {patch_output_path}")
                except Exception as e:
                    print(f"Failed to save patch: {patch_output_path}, error: {e}")
                    continue

                patch_coords = [
                    (x, y),
                    (x + patch_size, y),
                    (x + patch_size, y + patch_size),
                    (x, y + patch_size),
                ]
                patch_data[patch_name] = patch_coords

                patch_index += 1

    xml_output_path = os.path.join(output_dir, f"{os.path.basename(image_zarr_path)[:10]}inflammatory-cells.xml")
    create_combined_xml(image_zarr_path, patch_data, xml_output_path)


image_path = r'/input/images/kidney-transplant-biopsy-wsi-pas/.'
image_name = "/input/images/kidney-transplant-biopsy-wsi-pas/" + os.listdir(image_path)[0]
mask_path = r'/input/images/tissue-mask/.'
mask_name = "/input/images/tissue-mask/" + os.listdir(mask_path)[0]
# output_dir = "S:/GrandChallenge/Monkey/Dataset2/pure_patches/patches"
output_dir = "./Patches"

image_zarr_path = './zarr/large_image.zarr'
mask_zarr_path = './zarr/large_mask.zarr'

tiff_to_zarr(image_name, image_zarr_path)
tiff_to_zarr(mask_name, mask_zarr_path)

generate_patches_from_zarr(image_zarr_path, mask_zarr_path, output_dir)
