import json

cable_file_dir = "./"

def write_cable_to_json(data:dict):
	# if not os.path.isdir():
	# 	os.mkdir(cable_directory)

	with open(cable_file_dir + "current_cable.json", 'w') as f:
		json.dump(data, f, indent=4)

def load_json_cable():
	with open(cable_file_dir + "current_cable.json") as f:
		cable = json.load(f)
		 
	return cable

def update_json_field(key, value):
	cable = load_json_cable()

	if isinstance(value, list):
		cable[key] = []

	cable[key] = value
	write_cable_to_json(cable)