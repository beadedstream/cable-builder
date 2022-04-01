# Cable Builder App
A complete rebuild of the original 505 factory app with API itegration that works exclusively with the 605.

## Python Requirement:
For running the application with python you can run the script file [main.py](src/main.py). You need python version 3.8 or higher.

All packages needed to run the application that are not included within a standard python distribution are listed within [requirements.txt](requirements.txt).
They can be installed using the following:
```pip install -r requirements.txt```

## Compiling:
To compile and create a windows executable run the [build.bat](build.bat) file on windows. The exe and all the necessary files to run it will be dumped into zip folder within /dist which is created in the root directory.
### Compiling Requirements:
For compiling into an exe you need to have [pyinstaller](https://pypi.org/project/pyinstaller/) installed (can be installed with pip) as well as the console version of [7zip](https://www.7-zip.org/download.html) with a path variable linking to it.

(Skip this step; not implemented)
For Creating an installable executable run the build.bat file. [Inno Setup](https://jrsoftware.org/isdl.php) must be installed inorder to do this and a path variable needs to be created linking to the install path.

An exe can be generated with the follow terminal command though it should ONLY be done for testing since this is already done automatically when running the build.bat file:

```pyinstaller --onefile src/main.py```

## Tabs:
### Details
To run the app you need to have the D605N connected via uart cable inorder to unlock app functionally. To start with, you can click "Load using Serial" to pull cable info using a given serial or you can load a json file and paste the cable info in as well.
### Scan and Sort
Once you click scan sensors the 605 will constantly read and output all device ids from the port 1. You need to scan one sensor at a time until all sensors needed for that cable are scanned minus the sensor that share the same mold with the eeprom
### Build
Test cable to verify that all sensors are valid and not parasitically powered.
### Program
Upload meta and ids to the eeprom then test the cable again once all the molds are on it.

FYI:
Two commands you can run without the need to initiate cables are "find" which gets all the ids of each sensor on a given cable (in it's raw order) using a port and slot number as well "find_temps" which gets the temps from a a given cable using a port and slot number as well.

You can use these commands through realterm or the calibration app
