# c:\Python312_64\python convert_pt_to_onnx.py --pt example_pt\yolo11n.pt --v8 --onnx example_pt\yolo11n.onnx
import argparse
import torch
import os
import sys

def convert_yolov5(pt_path, onnx_path, imgsz):
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=pt_path)
    model.eval()

    dummy_input = torch.zeros((1, 3, imgsz, imgsz))
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        opset_version=12,
        input_names=['images'],
        output_names=['output'],
        dynamic_axes={'images': {0: 'batch'}, 'output': {0: 'batch'}},
        verbose=False
    )
    print(f"✅ YOLOv5 model exported to {onnx_path}")

def convert_yolov8(pt_path, onnx_path, imgsz):
    from ultralytics import YOLO
    model = YOLO(pt_path)
    export_result = model.export(
        format='onnx',
        imgsz=imgsz,
        dynamic=True,
        simplify=True,
        opset=12,             # 明確設定 opset
        half=False,           # 若你要支援 FP32
        device='cpu'          # 確保 ONNX 轉換穩定
    )

    # 輸出路徑修正（YOLO v8 會輸出到 runs\export\onnx\model.onnx）
    if not os.path.isfile(onnx_path):
        default_path = export_result.get("file")
        if default_path and os.path.isfile(default_path):
            os.rename(default_path, onnx_path)
            print(f"✅ YOLOv8 model exported and moved to {onnx_path}")
        else:
            print("❌ Exported ONNX file not found.")
    else:
        print(f"✅ YOLOv8 model exported to {onnx_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pt', type=str, required=True, help='Path to .pt model')
    parser.add_argument('--onnx', type=str, required=False, help='Output ONNX file path')
    parser.add_argument('--imgsz', type=int, default=640, help='Input image size (square)')
    parser.add_argument('--v8', action='store_true', help='Use this flag for YOLOv8')
    args = parser.parse_args()

    if not os.path.isfile(args.pt):
        print("❌ Error: .pt file not found")
        sys.exit(1)

    output_onnx = args.onnx if args.onnx else os.path.splitext(args.pt)[0] + ".onnx"

    if args.v8:
        convert_yolov8(args.pt, output_onnx, args.imgsz)
    else:
        convert_yolov5(args.pt, output_onnx, args.imgsz)