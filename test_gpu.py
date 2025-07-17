import torch
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
print("CUDA 是否可用:", torch.cuda.is_available())
print("可用 GPU 數量:", torch.cuda.device_count())
print("GPU 名稱:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")