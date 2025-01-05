#
# my_yolo.py example_pic\cat.jpg example_pic\out.jpg

from ultralytics import YOLO
import sys
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import json

names_cht_dict = {
    'person': '人物',
    'bicycle': '腳踏車',
    'car': '汽車',
    'motorcycle': '摩托車',
    'airplane': '飛機',
    'bus': '公車',
    'train': '火車',
    'truck': '卡車',
    'boat': '船',
    'traffic light': '紅綠燈',
    'fire hydrant': '消防栓',
    'stop sign': '停止標誌',
    'parking meter': '停車收費表',
    'bench': '長椅',
    'bird': '鳥',
    'cat': '貓',
    'dog': '狗',
    'horse': '馬',
    'sheep': '羊',
    'cow': '牛',
    'elephant': '大象',
    'bear': '熊',
    'zebra': '斑馬',
    'giraffe': '長頸鹿',
    'backpack': '背包',
    'umbrella': '雨傘',
    'handbag': '手提包',
    'tie': '領帶',
    'suitcase': '行李箱',
    'frisbee': '飛盤',
    'skis': '滑雪板',
    'snowboard': '滑雪板',
    'sports ball': '運動球',
    'kite': '風箏',
    'baseball bat': '棒球棒',
    'baseball glove': '棒球手套',
    'skateboard': '滑板',
    'surfboard': '衝浪板',
    'tennis racket': '網球拍',
    'bottle': '瓶子',
    'wine glass': '酒杯',
    'cup': '杯子',
    'fork': '叉子',
    'knife': '刀',
    'spoon': '湯匙',
    'bowl': '碗',
    'banana': '香蕉',
    'apple': '蘋果',
    'sandwich': '三明治',
    'orange': '橙子',
    'broccoli': '西蘭花',
    'carrot': '胡蘿蔔',
    'hot dog': '熱狗',
    'pizza': '披薩',
    'donut': '甜甜圈',
    'cake': '蛋糕',
    'chair': '椅子',
    'couch': '沙發',
    'potted plant': '盆栽植物',
    'bed': '床',
    'dining table': '餐桌',
    'toilet': '馬桶',
    'tv': '電視',
    'laptop': '筆記型電腦',
    'mouse': '滑鼠',
    'remote': '遙控器',
    'keyboard': '鍵盤',
    'cell phone': '手機',
    'microwave': '微波爐',
    'oven': '烤箱',
    'toaster': '烤麵包機',
    'sink': '水槽',
    'refrigerator': '冰箱',
    'book': '書',
    'clock': '時鐘',
    'vase': '花瓶',
    'scissors': '剪刀',
    'teddy bear': '泰迪熊',
    'hair drier': '吹風機',
    'toothbrush': '牙刷'
}


def get_dynamic_imgsz(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
    # 根據圖片大小調整 `imgsz`
    if max(width, height) > 2000:
        return 2048  # 適合處理高解析度圖片
    #elif max(width, height) > 1000:
    #    return 1280  # 中等大小圖片
    else:
        return 640   # 小尺寸圖片或細節為主

# Load a pretrained YOLOv8n model
model1 = YOLO("example_pt/yolo11n.pt")

# Load the second trained model
# model2 = YOLO("/var/www/html/park/yolo/runs/detect/train10/weights/best.pt")

# Load a font for Chinese text (make sure this font is installed on your system)
font = ImageFont.truetype("fonts/SimHei.ttf", 46)



# Run inference on the input image
results1 = model1.predict(sys.argv[1], imgsz=get_dynamic_imgsz(sys.argv[1]), conf=0.6)
#results2 = model2.predict(sys.argv[1], imgsz=640, conf=0.6)

#print(results2)
#sys.exit(1)

# Load the original image using OpenCV
image = cv2.imread(sys.argv[1])

# Get the size of the image
img_height, img_width, img_channels = image.shape

# Convert the image to RGB (PIL needs RGB format)
image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

# Create an ImageDraw object for drawing on the image
draw = ImageDraw.Draw(image_pil)

# 1. Draw text for results from model1

my_founds = []

for i, box in enumerate(results1[0].boxes.xyxy.tolist()):
    x1, y1, x2, y2 = map(int, box)  # Extract the coordinates of the bounding box
    label = int(results1[0].boxes.cls[i])  # Convert label to int if it's in float

    # Get the label name from model1
    label_name = results1[0].names[label]
    cht_label_name = names_cht_dict[label_name]
    
    txt_y = y1
    if y1 - 50 > 0:    
        txt_y = y1 - 55
    elif y2 + 50 > img_height:
        txt_y = y2 - 55
    else:
        txt_y = y2 + 1            
    #txt_y = y2 + 55 if (y1 - 50) < 0 else y1
    #txt_y = txt_y - 55
    # Use PIL to draw the Chinese text (green color)
    for offset in [(-2,-2), (-1, -2), (0, -2), ( 1, -2), ( 2,-2), 
                   (-2,-1), (-1, -1), (0, -1), ( 1, -1), ( 2,-1),
                   (-2, 0), (-1,  0), (0,  0), ( 1,  0), ( 2, 0),
                   (-2, 1), (-1,  1), (0,  1), ( 1,  1), ( 2, 1),
                   (-2, 2), (-1,  2), (0,  2), ( 1,  2), ( 2, 2)]:
        #draw.text((x + offset[0], y + offset[1]), text, font=font, fill="black")
        draw.text((x1 + offset[0], txt_y + offset[1]), f'{cht_label_name}', font=font, fill=(255, 255, 255))
    #draw.text((x1-1, txt_y - 46), f'{label_name}', font=font, fill=(255, 255, 255))
    #draw.text((x1, txt_y - 46), f'{label_name}', font=font, fill=(255, 255, 255))
    #draw.text((x1+1, txt_y - 46), f'{label_name}', font=font, fill=(255, 255, 255))
    
    #draw.text((x1-1, txt_y - 44), f'{label_name}', font=font, fill=(255, 255, 255))
    #draw.text((x1, txt_y - 44), f'{label_name}', font=font, fill=(255, 255, 255))
    #draw.text((x1+1, txt_y - 44), f'{label_name}', font=font, fill=(255, 255, 255))
    
    #draw.text((x1-1, txt_y - 45), f'{label_name}', font=font, fill=(255, 255, 255))
    #draw.text((x1+1, txt_y - 45), f'{label_name}', font=font, fill=(255, 255, 255))
        
    draw.text((x1, txt_y), f'{cht_label_name}', font=font, fill=(21, 123, 255))
# 2. Draw text for results from model2

'''
for i, box in enumerate(results2[0].boxes.xyxy.tolist()):
    x1, y1, x2, y2 = map(int, box)  # Extract the coordinates of the bounding box
    label = int(results2[0].boxes.cls[i])  # Convert label to int if it's in float

    
    # Get the label name from model2
    label_name = results2[0].names[label]
    confidence = results2[0].boxes.conf[i]  # Get the confidence score

    # Only draw box if confidence > 0.5
    if confidence < 0.5:
        continue
    # Use PIL to draw the Chinese text (green color)
    txt_y = y1
    if y1 - 50 > 0:    
        txt_y = y1 - 55
    elif y2 + 50 > img_height:
        txt_y = y2 - 55
    else:
        txt_y = y2 + 1   
    # Use PIL to draw the Chinese text (green color)
    for offset in [(-2,-2), (-1, -2), (0, -2), ( 1, -2), ( 2,-2), 
                   (-2,-1), (-1, -1), (0, -1), ( 1, -1), ( 2,-1),
                   (-2, 0), (-1,  0), (0,  0), ( 1,  0), ( 2, 0),
                   (-2, 1), (-1,  1), (0,  1), ( 1,  1), ( 2, 1),
                   (-2, 2), (-1,  2), (0,  2), ( 1,  2), ( 2, 2)]:
   
        draw.text((x1 + offset[0], txt_y + offset[1]), f'{label_name}', font=font, fill=(255, 255, 255))           
    draw.text((x1, txt_y), f'{label_name}', font=font, fill=(21, 123, 255))
'''
# Convert the image back to OpenCV format (BGR)
image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

# 3. Draw bounding boxes after text
# Draw results for model1 (blue bounding boxes)
for i, box in enumerate(results1[0].boxes.xyxy.tolist()):
    x1, y1, x2, y2 = map(int, box)  # Extract the coordinates of the bounding box
    # Use OpenCV to draw the bounding box (blue color)
    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Draw a blue box
    label = int(results1[0].boxes.cls[i])  # Convert label to int if it's in float

    # Get the label name from model1
    label_name = results1[0].names[label]
    cht_label_name = names_cht_dict[label_name]
    d = {
        "label": label_name,
        "cht_label": cht_label_name,
        "x1": x1,
        "x2": x2,
        "y1": y1,
        "y2": y2,
    }
    my_founds.append(d)    

# Draw results for model2 (green bounding boxes)
'''
for i, box in enumerate(results2[0].boxes.xyxy.tolist()):
    x1, y1, x2, y2 = map(int, box)  # Extract the coordinates of the bounding box
    # Use OpenCV to draw the bounding box (green color)
    confidence = results2[0].boxes.conf[i]  # Get the confidence score

    # Only draw box if confidence > 0.5
    if confidence < 0.5:
        continue
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw a green box
'''


# Save the result to the output file
cv2.imwrite(sys.argv[2], image)

# write txt
r_path = os.path.realpath(sys.argv[2])
dn = os.path.dirname(r_path)
# 提取檔案名稱（包含副檔名）
bn = os.path.basename(r_path)
mn, _ = os.path.splitext(bn)
# 輸出 txt
json_str = json.dumps(my_founds)
# 輸出到文字檔
output_path = os.path.join(dn, f"{mn}.txt")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(json_str)