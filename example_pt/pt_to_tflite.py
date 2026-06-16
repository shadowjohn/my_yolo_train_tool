from ultralytics import YOLO

model = YOLO('model1.pt')  # 或換成你自己的 pt
model.export(format='tflite')  # 會輸出 yolov8n.tflite