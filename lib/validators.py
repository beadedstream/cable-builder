from prompt_toolkit.validation import ValidationError, Validator
import re
from lib.api import API

is_port = Validator.from_callable(
	lambda text: text.isdigit() and len(text) == 1,
	error_message='Invalid port number',
	move_cursor_to_end=True)

def isValidSensorID(text:str):
	# 1A000001DD49E028
	sensor_match = re.compile(r'[A-F0-9]{16}', re.IGNORECASE)

	res = sensor_match.search(text)

	if res:
		return True

	return False

is_sensor_id = Validator.from_callable(
	isValidSensorID,
	error_message='This input is not a valid sensor id',
	move_cursor_to_end=True
)

class SerialValidator(Validator):
	def __init__(self, api:API):
		# uses the same api instance as main
		self.api = api
	def validate(self, document):
		text:str = document.text

		if text:
			# if cable is read by scanner, the output will be "DTC" + 4 digits for the serail number
			# scanner acts as keyboard input so text needs to be parsed here
			if text.find("DTC")  != 1:
				text = text.replace("DTC", "")

			if not text.isdigit():
				raise ValidationError(message='This input contains non-numeric characters', cursor_position=len(text)-1)

			elif len(text) != 4:
				raise ValidationError(message='Invalid serial number length', cursor_position=len(text)-1)

			error_msg = validate_api_call(self.api.get_cable_by_serial(text))
			if error_msg != "":
				raise ValidationError(message=error_msg, cursor_position=len(text)-1)
		else:
			raise ValidationError(message='Type a serial number', cursor_position=len(text)-1)

# needed for cases where user spams the enter key instead of giving a yes or no answer
class y_n_validator(Validator):
	def validate(self, document):
		text:str = document.text

		if text:
			if len(text) > 1:
				raise ValidationError(message='Invalid serial number length', cursor_position=len(text)-1)
		else:
			raise ValidationError(message='Type y or n', cursor_position=len(text)-1)

class user_validator(Validator):
	def validate(self, document):
		text:str = document.text

		if text:
			if len(text) < 2:
				raise ValidationError(message="Need more characters for a name", cursor_position=len(text)-1)
			else:
				for c in text:
					if c.isdigit():
						raise ValidationError(message="Cannot have digits in name unless your Elon's kid", cursor_position=len(text)-1)
		else:
			raise ValidationError(message='Type a name', cursor_position=len(text)-1)


def validate_api_call(response:dict):
	for key in response.keys():
		if key == 'error':
			return response[key]
		if response[key] == []:
			return "No record found in database"

	return ""