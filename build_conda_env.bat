rem 1. 下載、安裝 cuda 11.8 https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows
rem 2. 下載 Anaconda3-2024.10-1-Windows-x86_64.exe 安裝，安裝在 C:\anaconda3
rem https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Windows-x86_64.exe
rem 3. 設環境變數 Path 加入 C:\anaconda3\Scripts
rem 4. 安裝 yolo

SET mypath=%~dp0
echo %mypath%
mkdir binary
call conda create --prefix "%mypath%\binary\Ultralytics" python=3.10 -y
call conda activate "%mypath%\binary\Ultralytics"
cd /d "%mypath%\binary\Ultralytics"
rem call scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
rem call scripts\pip install -r ..\..\requirements.txt
rem ultralytics ?
call conda install -y pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
call scripts\pip install ultralytics pywin32 keyboard fastapi uvicorn
rem call scripts\pip install pywin32 keyboard flask ultralytics==8.0.186 torch==2.0.1 torchvision==0.15.2 tensorflow==2.13.0 onnx==1.13.1 onnx2tf==1.22.0 opencv-python==4.8.0.76 h5py==3.10.0 flatbuffers==24.3.25
rem call conda install -y tensorflow
rem call scripts\pip install tensorflow-cpu==2.10.0


