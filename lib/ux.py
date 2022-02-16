from prompt_toolkit import prompt


def getCable(api, serial):
    # get cable
    cable = api.get_cable_by_serial(serial)
    if 'error' in cable.keys():
        print('error getting cable', cable['error'])

    return cable['cables'][-1]


def calibrateCable(api, cable_id):
    cableEvent = {
        "action": "calibrate",
        "operator": prompt("Enter operator initials: "),
        "notes": prompt("Enter notes: "),
    }
    calibrationEvent = api.create_cable_event(cable_id, cableEvent)
    if 'error' in calibrationEvent.keys():
        print('error creating cable event', calibrationEvent['error'])

    return calibrationEvent


def calibrateSensor(api, serial, sensor, cable, calibration_id):
    res = api.get_sensor(sensor['id'])
    if 'error' in res.keys():
        # create sensor if not exists
        sensor = {
            'id': sensor['id'],
            'cable': [{
                'serial': int(serial),
                'mold': '',
                'units': {
                    'length': ''
                },

                'calibration_id': calibration_id,
                'offset': '',
                'position': sensor['position'],
                'spacing': '',
            }]
        }
        api.create_sensor(sensor)

    else:
        # update existing sensor
        sensorCalibration = {
            "serial": serial,
            "position": 0,
            "offset": 0,
            "spacing": 0,
            "calibration_id": calibration_id
        }
        sensorEvent = api.calibrate_sensor(
            sensor['id'], sensorCalibration)
        if 'error' in sensorEvent.keys():
            print('error creating sensor event', sensorEvent['error'])
