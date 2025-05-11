rem rd /S build
rem -w --clean
SET mypath=%~dp0
echo %mypath%
C:\Windows\System32\chcp.com 65001 && set PYTHONIOENCODING=utf-8 && conda run --prefix "%mypath%\binary\Ultralytics" "%mypath%\binary\Ultralytics\scripts\pyinstaller.exe" -F --onefile --icon="pic\icon.ico" --version-file=metadata.txt ^
--exclude-module=_ssl ^
--exclude-module=_bz2 ^
--exclude-module=_lzma ^
--exclude-module=pyconfig ^
--exclude-module=pytorch ^
--exclude-module=torch ^
--exclude-module=sqlite3 ^
--exclude-module=pandas ^
--exclude-module=IPython ^
--exclude-module=scipy ^
--exclude-module=pygments ^
--exclude-module=pyinstaller ^
--exclude-module=tensorflow ^
--exclude-module=unittest ^
--exclude-module=doctest ^
--exclude-module=pillow ^
--exclude-module=av ^
--exclude-module=setuptools ^
--add-data=www:www ^
my_yolo_train_tool.py

rem --exclude-module=PIL ^