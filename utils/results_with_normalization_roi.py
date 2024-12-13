import json
import os
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, Point
from ultralytics import YOLO
import rasterio
import numpy as np


CLASSES = ["lymphocytes", "monocytes"]

# Parse XML and extract ROIs and patch offsets
def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    rois = []
    patches = {}

    for annotation in root.find("Annotations"):
        name = annotation.get("Name")
        annotation_type = annotation.get("Type")
        coordinates = annotation.find("Coordinates")

        if annotation_type == "Polygon" and "ROI" in name:
            # Extract ROI as a polygon
            roi_points = []
            for coord in coordinates.findall("Coordinate"):
                x = float(coord.get("X"))
                y = float(coord.get("Y"))
                roi_points.append((x, y))
            rois.append(Polygon(roi_points))

        elif "Patch" in name and annotation_type == "Rectangle":
            # Extract patch offset (top-left corner)
            x_tl = float(coordinates.find("Coordinate[@Order='0']").get("X"))
            y_tl = float(coordinates.find("Coordinate[@Order='0']").get("Y"))
            patches[name] = (x_tl, y_tl)

    return rois, patches


# Convert YOLO detections to JSON format
def detections_to_json(detections, class_name, output_file):
    output_data = {
        "name": class_name,
        "type": "Multiple points",
        "points": [],
        "version": {"major": 1, "minor": 0},
    }

    for idx, (x, y, conf) in enumerate(detections):
        output_data["points"].append(
            {
                "name": f"Point {idx + 1}",
                "point": [x, y, 0.25],  # Default spacing
                "probability": round(conf, 2),
            }
        )

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)
    print(f"JSON saved to {output_file}")


def is_point_in_mask(x, y, mask_data):
    """
    Simple check if the point lies within the bounds of the binary mask.
    Args:
        x (float): X coordinate.
        y (float): Y coordinate.
        mask_data (ndarray): 2D numpy array representing the binary mask.

    Returns:
        bool: True if the detection point is in the ROI defined by mask_data.
    """
    # Convert the world coordinates to pixel indices assuming identity mapping
    row, col = int(round(y)), int(round(x))

    # Ensure indices are within bounds
    if 0 <= row < mask_data.shape[0] and 0 <= col < mask_data.shape[1]:
        return mask_data[row, col] > 0  # Check if the point is part of the ROI
    return False



model = YOLO('./best.pt')

image_directory = "./Patches"
xml_directory = "./Patches"
mask_path = r'./data/ROI_masks/.'
mask_name = "./data/ROI_masks/" + os.listdir(mask_path)[0]


with rasterio.open(mask_name) as src:
    mask_data = src.read(1)  # Load the first band from the mask.tif
    transform = src.transform  # Extract spatial transform for mapping coordinates

# Parse all XML files to build ROI and patch metadata
rois_by_base_name = {}
patch_to_offset = {}
for xml_file in os.listdir(xml_directory):
    if xml_file.endswith(".xml"):
        print(f"Processing XML file: {xml_file}")
        base_name = os.path.splitext(xml_file)[0]  # Extract the base name
        rois, patches = parse_xml(os.path.join(xml_directory, xml_file))
        rois_by_base_name[base_name] = rois
        patch_to_offset[base_name] = patches

results = model(image_directory)

detections_by_class = {cls: [] for cls in CLASSES}
inflammatory_detections = []  

for result in results:
    patch_name = os.path.splitext(os.path.basename(result.path))[0]
    print(f"Processing image: {patch_name}")
    
    # Extract base name without suffix
    base_name = "_".join(patch_name.split("_")[:-1])
    if base_name not in patch_to_offset or base_name not in rois_by_base_name:
        print(f"Warning: No metadata found for {patch_name}")
        continue

    # Get ROI polygons and patch offsets
    rois = rois_by_base_name[base_name]
    patches = patch_to_offset[base_name]

    # Get patch offset
    patch_index = int(patch_name.split("_")[-1])
    patch_key = f"Patch_{patch_index}"
    if patch_key not in patches:
        print(f"Warning: No patch offset found for {patch_key} in {base_name}")
        continue
    x_offset, y_offset = patches[patch_key]

    # Process detections
    boxes = result.boxes
    for box in boxes:
        # Map detection coordinates with offsets
        x_center = float((box.xywh[0][0]).item()) + x_offset
        y_center = float((box.xywh[0][1]).item()) + y_offset
        conf = float(box.conf[0].item())
        cls = int(box.cls[0].item())

        # Check against the mask
        if is_point_in_mask(x_center, y_center, mask_data):
            class_name = CLASSES[cls]
            detections_by_class[class_name].append((x_center, y_center, conf))
            inflammatory_detections.append((x_center, y_center, conf))

# Save results as JSON
for class_name, detections in detections_by_class.items():
    output_file = f"detected-{class_name.replace('_', '-')}.json"
    detections_to_json(detections, class_name, output_file)

output_file = "detected-inflammatory-cells.json"
detections_to_json(inflammatory_detections, "inflammatory-cells", output_file)
