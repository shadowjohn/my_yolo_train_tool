from ultralytics import YOLO
import os
_model = YOLO(os.path.join("data","projects","三國迷因","train_project","task_1752742761","best.pt"))
_model.export(format="tflite",simplify=True,optimize=True)