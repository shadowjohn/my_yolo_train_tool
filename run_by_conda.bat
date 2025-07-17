SET mypath=%~dp0
echo %mypath%
call conda activate "%mypath%\binary\Ultralytics"
"%mypath%\binary\Ultralytics\python.exe" my_yolo_train_tool.py