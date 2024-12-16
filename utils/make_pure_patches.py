from tifffile import TiffFile, imwrite
import os
import numpy as np
import xml.etree.ElementTree as ET


def create_combined_xml(tiff_name, patch_data, output_file):
    """
    Creates a single XML file containing information for all patches, their centers, and ROI polygons.
    """
    root = ET.Element("ASAP_Annotations")
    annotations = ET.SubElement(root, "Annotations")

    for patch_index, (patch_name, patch_coords) in enumerate(patch_data.items()):
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

        annotation = ET.SubElement(annotations, "Annotation", {
            "Name": f"Patch_{patch_index}",
            "Type": "Rectangle",
            "PartOfGroup": "None",
            "Color": "255, 0, 0"
        })
        coords = ET.SubElement(annotation, "Coordinates")
        for i, (x, y) in enumerate(patch_coords):
            ET.SubElement(coords, "Coordinate", {"Order": str(i), "X": str(x), "Y": str(y)})





def generate_patches_from_mask_and_image(image_path, mask_path, output_dir, patch_size=1024):
    """
    Generates patches from a large image and mask. Saves non-empty image patches to output_dir and 
    creates a combined XML file with patch metadata.
    """
    os.makedirs(output_dir, exist_ok=True)

    patch_index = 0
    patch_data = {}


    with TiffFile(image_path) as tif_image, TiffFile(mask_path) as tif_mask:
        image_reader = tif_image.pages[0] 
        mask_reader = tif_mask.pages[0]  

        y = 0
        while True:
            x = 0
           
            row_empty = True  
            while True:
                row_slice = slice(y, y + patch_size)
                col_slice = slice(x, x + patch_size)
                print(f"{x} {y}")
                try:
                    mask_patch = mask_reader.asarray()[row_slice, col_slice]

                    if np.any(mask_patch):  
                        row_empty = False

                        image_patch = image_reader.asarray()[row_slice, col_slice]

                        patch_name = f"{os.path.splitext(os.path.basename(image_path))[0][:10]}_patch_{patch_index}"
                        patch_output_path = os.path.join(output_dir, f"{patch_name}.png")
                        imwrite(patch_output_path, image_patch)

                        patch_coords = [
                            (x, y),
                            (x + patch_size, y),
                            (x + patch_size, y + patch_size),
                            (x, y + patch_size),
                        ]
                        patch_data[patch_name] = patch_coords

                        patch_index += 1

                    x += patch_size

                except IndexError:
                    # Break when reaching the end of the row
                    break

            if row_empty:
                break

            y += patch_size

   

    # Create a single combined XML for this TIFF
    xml_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0][0:10]}inflammatory-cells.xml")
    #create_combined_xml(image_path, patch_data, roi_coordinates, xml_output_path)
    create_combined_xml(image_path, patch_data, xml_output_path)

    #print(f"Patches and XML annotations saved in {output_dir}")



# Example usage
#image_path = r'/input/images/kidney-transplant-biopsy-wsi-pas/.' 
#image_name = "/input/images/kidney-transplant-biopsy-wsi-pas/" + os.listdir(image_path)[0]
#mask_path = r'/input/images/tissue-mask/.' 

#mask_name = "/input/images/tissue-mask/" + os.listdir(mask_path)[0]
output_dir = "./Patches"

# Generate patches
#generate_patches_from_mask_and_image(image_name, mask_name, output_dir)
generate_patches_from_mask_and_image("A_P000001_PAS_CPG.tif", "A_P000001_mask.tif", output_dir)
