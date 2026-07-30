import json

data = r"D:\orlen_fotowoltaika\project_data.json"



with open(data, "r") as file:
    json_data = json.load(file)


image_name = "DJI_20240829131300_0002_T.tif"

neighbors = ["DJI_20240829131259_0001_T.tif", "DJI_20240829131301_0003_T.tif"]

for neighbor_id in filter(None, neighbors):

    image = json_data["images"][neighbor_id].get("thermal_path")

    print(image)