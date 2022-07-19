pyinstaller.exe --onefile --console --name D605_Cable_Builder --icon="../logos/icon.ico" --distpath ../dist ../main_window.py

:: rmdir /s /q ..\__pycache__
rmdir /s /q build

7za a "..\dist\D605_Cable_Builder.zip" "..\ui\" "..\dist\D605_Cable_Builder.exe"
del ..\dist\*.exe
:: iscc installer_script.iss (will add this later) 