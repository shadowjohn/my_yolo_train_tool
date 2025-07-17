rem 1. 下載、安裝 cuda 11.8 https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows
rem 2. 下載 Anaconda3-2024.10-1-Windows-x86_64.exe 安裝，安裝在 C:\anaconda3
rem https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Windows-x86_64.exe
rem 3. 設環境變數 Path 加入 C:\anaconda3\Scripts
rem 4. 安裝 yolo

SET mypath=%~dp0
echo %mypath%
mkdir binary
call conda create --prefix "%mypath%\binary\Ultralytics" python=3.9 -y
call conda activate "%mypath%\binary\Ultralytics"
cd /d "%mypath%\binary\Ultralytics"
rem call scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
rem call scripts\pip install -r ..\..\requirements.txt
rem ultralytics ?
call conda install -y pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
call scripts\pip install ultralytics pywin32 keyboard flask


