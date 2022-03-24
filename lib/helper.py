from colorama import Style, Fore

def convert_to_mm(value:float, units:str):

	conversion_val:float = 0
	
	if units == 'ft':
		conversion_val = 304.8 #ft to millimeters
	elif units == 'cm':
		conversion_val = 10 #cm to millimeters
	elif units == 'm':
		conversion_val = 1000 #m to millimeters
	else:
		print("Unrecongized units found. Fix before continuing")

	return int(round(value * conversion_val, 0)) # nearest mm

def convert_mm_to_dimension(value:int, units:str):

	if units == 'cm':
		return round(float(value * 0.1), 1)
	if units == 'm':
		return round(float(value * 0.001), 3)
	if units == 'in':
		return round(float(value * (1/25.4)), 3)
	if units == 'ft':
		return round(float(value * (1/304.8)), 3)

	return value

def close_application(msg:str, is_err = False):
	if is_err:
		print(Fore.RED + Style.BRIGHT + msg + Style.RESET_ALL)
	else:
		print(msg)
		
	input("Press enter to quit...")
	quit()

def write_to_log(text: str):
	with open("log.txt", "a") as f:
		f.write(text + "\n")