from requests import Session, Request
import json
import datetime

BASE_URI = "https://bsapi.tnpi.net/api/v1"

user = {
    "username": "kyler.nelson@beadedstream.com",
    "password": "iJ6FKA8AUZ4C"
}

def pretty_print_request(req):
    print('{}\n{}\r\n{}\r\n\r\n{}\n\n'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v)
                    for k, v in req.headers.items()),
        req.body,
    ))


class API:
    def __init__(self, print_request=False, print_response=False):
        self.session = Session()
        self.print_request = print_request
        self.print_response = print_response
        self.login(user)
        self.name = ""
        # self.password = ""

    def api_request(self, request_type, endpoint, error_message, json_data=None, params={}, base_URI=BASE_URI, admin=True):

        if admin:
            params['admin'] = 'true'
        url = base_URI+endpoint

        # print(url)

        try:

            req = self.session.prepare_request(
                Request(request_type, base_URI + endpoint, params=params, json=json_data))

            if self.print_request:
                pretty_print_request(req)

            resp = self.session.send(req)

            if self.print_response:
                print(resp.json())

            return resp.json()

        except:
            print("Encountered error when " + error_message + ".")

    def GET(self, endpoint, error_message, params={}, admin=True):
        return self.api_request('GET', endpoint, error_message, params=params, admin=admin)

    def PUT(self, endpoint, error_message, params={}, json_data=None, admin=False):
        return self.api_request('PUT', endpoint, error_message,
                                json_data=json_data, params=params, admin=admin)

    def POST(self, endpoint, error_message, params={}, json_data=None, admin=False):
        return self.api_request('POST', endpoint, error_message,
                                json_data=json_data, params=params, admin=admin)

    def DELETE(self, endpoint, error_message, params={}, json_data=None, admin=False):
        return self.api_request('DELETE', endpoint, error_message,
                                json_data=json_data, params=params, admin=admin)

    def login(self, userDetails):
        resp = self.POST('/user/session/', 'logging in user', json_data=userDetails)
        if 'error' not in resp.keys():
            user_data = resp["user"]["name"]
            self.name = user_data["first"] + ' ' + user_data["last"]

        return resp

    def logout(self):
        return self.DELETE('/user/session/', 'logging out user')

    def get_cable(self, cable_id):
        return self.GET('/cable/'+str(cable_id), 'fetching cable')

    def get_cable_by_serial(self, serial_num):
        params = {
            "serial": str(serial_num)
        }
        return self.GET('/cable/', 'fetching cable', params=params)

    def get_sensor(self, sensor_id):
        return self.GET('/sensor/'+str(sensor_id), 'fetching sensor')

    def get_sensors_by_serial(self, serial_num):
        params = {
            "cable.serial": str(serial_num)
        }
        return self.GET('/sensor/', 'fetching sensor', params=params)

    def get_reading(self, reading_id):
        return self.GET('/reading/'+str(reading_id), 'fetching reading')

    def create_sensor(self, sensor_obj):
        return self.POST('/sensor/', 'posting sensor', json_data=sensor_obj)

    def update_sensor(self, sensor_obj):
        return self.PUT('/sensor/'+str(sensor_obj['id']), 'updating sensor', json_data=sensor_obj)

    def update_cable(self, cable_obj):
        return self.PUT('/cable/'+str(cable_obj["cables"][-1]['id']), 'updating sensor', json_data=cable_obj)

    def get_cable_build_by_serial(self, serial):
        params = {
            "serial": str(serial)
        }
        return self.GET('/cableBuilder/', 'fetching cablebuilder data', params=params)

    def generate_calibation_id(self, serial, operator=None, notes = ""):
        data:dict = {
            "action": "calibrate",
            "notes": notes,
            "operator": self.name
        }

        if operator != None:
            data["operator"] = operator

        return self.PUT('/cable/'+ serial + '/event', 'fetching cablebuilder data', json_data=data)

    def get_project_from_serial(self, serial):
        try:
            proj_id = self.get_cable_by_serial(
                serial)['cables'][-1]['project']['id'][-1]
        except:
            print("encountered error when fetching project info from cable")
            return None

        return self.GET('/project/'+str(proj_id), 'fetching project')

    def create_cable_event(self, id, event):
        return self.PUT('/cable/'+str(id)+'/event', 'creating cable event', json_data=event)

    def calibrate_sensor(self, id, body):
        return self.PUT('/sensor/'+str(id)+'/calibrate', 'calibrating sensor', json_data=body)

    def parse_sensors(self, serial):

        # NOTE if you pull the senors for a given cable you may grab duplicates with invalid id's that were created by the old website
        # this method filters those out
        sensors = self.get_sensors_by_serial(serial)

        if type(sensors) == str:
            return 'Error occurred when fetching sensors'
        if 'error' in sensors:
            return sensors

        sensors = sensors['sensors']
        # if sensors.status_code >= 200 and sensors.status_code <= 201:
        ordered_sensors = []

        for i in range(len(sensors)-1, -1, -1):
            if sensors[i]['id'].find('DUMMY') != -1:
                sensors.pop(i)
                continue
            if 'order' in sensors[i]:
                if not 'updated' in sensors[i]['ts']:
                    sensors[i]['ts']['updated'] = sensors[i]['ts']['created']
                ordered_sensors.append(sensors[i])

        if len(ordered_sensors) != 0:  # order replaces position when db updates
            sensors = sorted(
                ordered_sensors, key=lambda sensor: sensor['order'])
            last_position = sensors[-1]['order']
        else:
            sensors = sorted(sensors, key=lambda sensor: sensor['position'])
            last_position = sensors[-1]['position']

        sensors_found = len(sensors)
        if last_position == sensors_found:
            return sensors

        try:
            sensors = sorted(sensors, key=lambda sensor: (sensor['position'], datetime.datetime.strptime(
                sensor['ts']['updated'], '%Y-%m-%dT%H:%M:%S.%fZ')))

        except:
            return 'Error sorting data'

        valid_sensors = []
        if sensors_found % last_position != 0:
            return 'Missing sensor(s) in database'

        duplicates = int(sensors_found / last_position)

        for i in range(sensors_found):
            if (i+1) % duplicates == 0:
                valid_sensors.append(sensors[i])

        return valid_sensors

if __name__ == "__main__":
    api = API()
    #print(api.get_sensors_by_serial("4004"))
    
    print(api.get_cable_by_serial("2175"))

	# functions = [
	# 	"login",
	# 	"logout",
	# 	"get_cable",
	# 	"get_cable_by_serial",
	# 	"get_sensor",
	# 	"get_sensors_by_serial",
	# 	"get_reading",
	# 	"post_sensor",
	# 	"update_sensor",
	# 	"build_cable_by_serial",
	# 	"get_project_from_serial",
	# 	"parse_sensors",
	# ]

	# while True:
	# 	userInput = input(
	# 		"enter a function name, followed by the needed args: ")
	# 	try:
	# 		args = userInput.split(' ')
	# 		if args[0] in functions:
	# 			if args[0] == 'login':
	# 				print(
	# 					api.login({'username': args[1], 'password': args[2]}))
	# 			else:
	# 				print(api.__getattribute__(args[0])(*args[1:]))

	# 		else:
	# 			print("function not found")

	# 		print()

	# 	except Exception as e:
	# 		print(e.message)

# if __name__ == "__main__":
#     api = API()


    # print(api.login(user))

#     # api.login(user)

    # print(len(api.parse_sensors('4003')))

#     # api.parse_metadata()

#     # print(api.get_cable("2"))

#     # print(api.get_cable(""))

#     # print(api.get_sensor("A54C3F1038E90A36"))

#     # print(api.get_reading("1"))

#     # print(api.get_cable_by_serial("4043"))

#     # print(api.logout())

#     # print(api.build_cable_by_serial("4043"))

#     # print(api.get_project_from_serial('4049'))

#     # print(api.parse_sensors("3646"))

#     # print(api.post_sensors("4004"))

#     # print(api.get_project_from_serial("2"))

#     # print(api.get_sensors_by_serial('3646'))

#     print(api.parse_sensors("4049"))

#     # print(api.get_cable_by_serial('3369')['cables'][-1]['project']['id'][-1])
