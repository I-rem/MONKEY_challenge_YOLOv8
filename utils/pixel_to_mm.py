import json
import os

# Conversion factor: 0.24 µm per pixel, converted to mm
PIXEL_TO_MM = 0.00024

def convert_json_to_mm(json_file, output_file=None):
    # Read the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Update the coordinates
    for point in data.get("points", []):
        x, y, z = point["point"]
        point["point"] = [(x * PIXEL_TO_MM ),(y * PIXEL_TO_MM), z]  # Convert x and y to mm
    
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    else:
        output_file = json_file  # Default to overwrite the original file

    # Save the updated JSON
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Converted JSON saved to {output_file}")

# Directory containing JSON files
#json_directory = "S:/GrandChallenge/Monkey/Dataset2/Yolo/runs/normalization_test/single_image_test/anots"
json_directory = "."
#output_directory = "S:/GrandChallenge/Monkey/Dataset2/Yolo/runs/normalization_test/single_image_test/anots_mm"  # Set this if you want to save to a different directory
output_directory = "./output"  


# Convert all JSON files in the directory
for file in os.listdir(json_directory):
    if file.endswith(".json"):
        json_file_path = os.path.join(json_directory, file)
        output_file_path = os.path.join(output_directory, file) if output_directory else json_file_path
        print(f"Processing {json_file_path}")
        convert_json_to_mm(json_file_path, output_file=output_file_path)
