import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import Menu
from tkinter import simpledialog
from tkinter import Label, Tk, StringVar
import threading
import os
import webbrowser
import sys
import base64
import portalocker
import mss
import php
import keyboard
from flask import Flask, render_template, jsonify, request, send_from_directory
from ctypes import windll, byref, sizeof, c_int, wintypes
from ctypes.wintypes import HWND, LONG, RECT
import requests
import subprocess
import signal
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil
import stat

names_cht_dict = {
    "person": "人物",
    "bicycle": "腳踏車",
    "car": "汽車",
    "motorcycle": "摩托車",
    "airplane": "飛機",
    "bus": "公車",
    "train": "火車",
    "truck": "卡車",
    "boat": "船",
    "traffic light": "紅綠燈",
    "fire hydrant": "消防栓",
    "stop sign": "停止標誌",
    "parking meter": "停車收費表",
    "bench": "長椅",
    "bird": "鳥",
    "cat": "貓",
    "dog": "狗",
    "horse": "馬",
    "sheep": "羊",
    "cow": "牛",
    "elephant": "大象",
    "bear": "熊",
    "zebra": "斑馬",
    "giraffe": "長頸鹿",
    "backpack": "背包",
    "umbrella": "雨傘",
    "handbag": "手提包",
    "tie": "領帶",
    "suitcase": "行李箱",
    "frisbee": "飛盤",
    "skis": "滑雪板",
    "snowboard": "滑雪板",
    "sports ball": "運動球",
    "kite": "風箏",
    "baseball bat": "棒球棒",
    "baseball glove": "棒球手套",
    "skateboard": "滑板",
    "surfboard": "衝浪板",
    "tennis racket": "網球拍",
    "bottle": "瓶子",
    "wine glass": "酒杯",
    "cup": "杯子",
    "fork": "叉子",
    "knife": "刀",
    "spoon": "湯匙",
    "bowl": "碗",
    "banana": "香蕉",
    "apple": "蘋果",
    "sandwich": "三明治",
    "orange": "橙子",
    "broccoli": "西蘭花",
    "carrot": "胡蘿蔔",
    "hot dog": "熱狗",
    "pizza": "披薩",
    "donut": "甜甜圈",
    "cake": "蛋糕",
    "chair": "椅子",
    "couch": "沙發",
    "potted plant": "盆栽植物",
    "bed": "床",
    "dining table": "餐桌",
    "toilet": "馬桶",
    "tv": "電視",
    "laptop": "筆記型電腦",
    "mouse": "滑鼠",
    "remote": "遙控器",
    "keyboard": "鍵盤",
    "cell phone": "手機",
    "microwave": "微波爐",
    "oven": "烤箱",
    "toaster": "烤麵包機",
    "sink": "水槽",
    "refrigerator": "冰箱",
    "book": "書",
    "clock": "時鐘",
    "vase": "花瓶",
    "scissors": "剪刀",
    "teddy bear": "泰迪熊",
    "hair drier": "吹風機",
    "toothbrush": "牙刷",
}

# 測試 Model
model = None


# Windows 專用功能：設置窗口滑鼠穿透
def set_window_exclude(window_id):
    return
    hwnd = wintypes.HWND(window_id)
    # 獲取當前窗口屬性
    exstyle = windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE = -20
    # 添加透明與滑鼠穿透屬性
    exstyle |= 0x20  # WS_EX_TRANSPARENT
    exstyle |= 0x80000  # WS_EX_LAYERED
    windll.user32.SetWindowLongW(hwnd, -20, exstyle)
    # 設置窗口完全透明 (僅顯示繪製的內容)
    windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x2)  # LWA_ALPHA = 0x2


# run_desktop_example 執行桌面範例
def run_desktop_example():
    # 按鈕名稱變成 - 停止
    # 再按一次按鈕，就會停止
    global is_run_keep_screen_predict
    if (
        GDATA["UI"]["btn_desktop_example_button"].config("text")[-1]
        == "桌面範例(運作中)"
    ):
        GDATA["UI"]["btn_desktop_example_button"].config(text="桌面範例(已停止)")
        # os.system("taskkill /F /IM run_desktop_flask_example.bat")

        # 結束 run_keep_screen_predict 裡的 while True
        is_run_keep_screen_predict = False
        return
    # 按鈕名稱變成 - 運作中
    GDATA["UI"]["btn_desktop_example_button"].config(text="桌面範例(運作中)")

    # 取得進程的 PID
    # pid = process.pid
    # print(f"進程 PID: {pid}")
    is_run_keep_screen_predict = True

    # 持續獲取桌面大小，一直辨識
    # 用 thread 嗎
    # 用 mss 這個套件
    # 用 requests 傳到 flask
    # 程式開始
    global model
    if model == None:
        model = YOLO("example_pt/yolo11x.pt")

    # 使用者需框選螢幕範圍給 YOLO 預測，才不會一直辨識整個螢幕
    # 用 tkinter 的 Toplevel 來做
    # 用透明視窗來畫框
    select_area_for_model()

    threading.Thread(target=run_keep_screen_predict, args=()).start()


is_run_keep_screen_predict = False
run_desktop_flask_example_PID = None


def get_dynamic_imgsz(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
    # 根據圖片大小調整 `imgsz`
    if max(width, height) > 2000:
        return 2048  # 適合處理高解析度圖片
    # elif max(width, height) > 1000:
    #    return 1280  # 中等大小圖片
    else:
        return 640  # 小尺寸圖片或細節為主


def run_keep_screen_predict():
    # 用 conda 背景啟動 yolo-env 環境的 python my_yolo_flask.py
    # 啟動進程
    # "conda activate ./yolo-env && python my_yolo_flask.py"
    global run_desktop_flask_example_PID
    global overlay_window
    global GDATA
    # process = subprocess.Popen("run_desktop_flask_example.bat", shell=False)
    # _screen_rects = []

    while True:
        global is_run_keep_screen_predict
        if is_run_keep_screen_predict == False:
            # 結束進程
            # 終止該進程
            # os.kill(pid, signal.SIGTERM)
            # 終止子進程
            # 清除畫框
            overlay_window.clear()

            # 清除畫框
            if "overlay_model" in GDATA and GDATA["overlay_model"] != None:
                GDATA["overlay_model"].destroy()
                GDATA["overlay_model"] = None

            # for rect in _screen_rects:
            #    rect.destroy()
            #    _screen_rects = []
            """pid = process.pid
            try:
                os.kill(pid, signal.SIGTERM)  # CTRL_C_EVENT)
            except:
                pass
            try:
                os.kill(pid, signal.CTRL_C_EVENT)
            except:
                pass
            try:
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            except:
                pass
            try:
                process.terminate()
                # 等待進程結束
                process.wait()
            except:
                pass
            # 確認進程已結束
            if process.returncode is not None:
                print(f"Process terminated with return code {process.returncode}")
            else:
                print("Process is still running.")
            if run_desktop_flask_example_PID != None:
                try:
                    os.kill(run_desktop_flask_example_PID, signal.SIGTERM)
                except:
                    pass
            """
            break
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                # 改用框的範圍

                rect = (
                    # monitor["left"],
                    # monitor["top"],
                    # monitor["width"],
                    # monitor["height"],
                    GDATA["x1_model"],
                    GDATA["y1_model"],
                    GDATA["x2_model"],
                    GDATA["y2_model"]
                )
                # print(rect)
                # 獲取桌面截圖
                sct_img = sct.grab(rect)
                # 顯示截圖
                img = np.array(sct_img)
                # 傳到 localhost 5000 flask 進行預測
                """
                url = "http://127.0.0.1:5000/predict"
                files = {
                    "file": (
                        "screenshot.png",
                        cv2.imencode(".png", img)[1].tobytes(),
                        "image/png",
                    )
                }
                response = requests.post(url, files=files)
                run_desktop_flask_example_PID = response.json()["pid"]
                # 如果有預測結果，就顯示在畫面上
                print(response.json())
                #print(response.text)"""
                #  img 存成暫存檔

                # temp_dir = tempfile.mkdtemp()
                # input_path = os.path.join(temp_dir, "screenshot.jpg")
                # my.file_put_contents(input_path,cv2.imencode(".jpg", img)[1].tobytes())
                # my.file_put_contents("C:\\temp\\a.jpg",cv2.imencode(".jpg", img)[1].tobytes())

                # 使用 YOLO 模型進行預測
                # get_dynamic_imgsz(input_path)
                # results = model.predict(input_path, imgsz=get_dynamic_imgsz(input_path), conf=0.6)[0]
                # Class indices (e.g., 0 for 'person', 1 for 'car')
                # 轉換成模型的輸入格式，通常是 (1, C, H, W)
                # img = np.moveaxis(img, -1, 0)  # 把維度轉換為 C, H, W
                # img = np.expand_dims(img, axis=0)  # 加上 batch 维度
                # 正規化 (如果需要的話)
                # img = img / 255.0  # 讓像素值在 0 到 1 之間
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                # , imgsz=2048
                desired_classes = [0, 1]
                results = model.predict(
                    img, imgsz=1024, conf=0.6 #, classes=desired_classes
                )[0]

                # shutil.rmtree(temp_dir)
                overlay_window.clear()
                # output = {
                #    "status": "OK",
                #    #"pid": _PID,
                #    "data": []
                # }
                for i, box in enumerate(results.boxes.xyxy.tolist()):
                    x1, y1, x2, y2 = map(int, box)
                    label = int(results.boxes.cls[i])
                    confidence = results.boxes.conf[i]
                    label_name = results.names[label]
                    # cht_label_name = names_cht_dict.get(label_name, label_name)
                    # 加回傳自身的 process id
                    overlay_window.create_rectangle(
                        x1 + GDATA["x1_model"],
                        y1 + GDATA["y1_model"],
                        x2 + GDATA["x1_model"],
                        y2 + GDATA["y1_model"],
                    )
                    # output["data"].append({
                    #    "label": label_name,
                    #    "label_cht": cht_label_name,
                    #    "confidence": round(float(confidence), 2),
                    #    "bbox": [x1, y1, x2, y2],
                    #    #"pid": _PID
                    # })
                # data_list = output["data"]
                # 清除畫框
                # for rect in _screen_rects:
                #    rect.destroy()
                #    _screen_rects = []

                # for data in data_list:
                #    x1, y1, x2, y2 = data["bbox"][0], data["bbox"][1], data["bbox"][2], data["bbox"][3]
                #    #cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                #    # 螢幕畫方框
                #    #_screen_rects.append(create_overlay_window(x1, y1, x2, y2))
                #    overlay_window.create_rectangle(x1, y1, x2, y2)

        except Exception as e:
            print(e)
            pass
    pass


class OverlayWindow:
    def __init__(self, root):
        # 創建透明的 Toplevel 視窗
        self.overlay = tk.Toplevel(root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 1)  # 透明度
        self.overlay.attributes("-transparentcolor", "black")  # 透明背景顏色
        self.overlay.configure(background="black")
        self.overlay.overrideredirect(True)  # 移除工作列圖示

        # 創建畫布
        self.canvas = tk.Canvas(self.overlay, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # 紀錄矩形框的列表
        self.rectangles = []

    def create_rectangle(self, x1, y1, x2, y2):
        # 繪製矩形框並儲存矩形對象
        rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)
        self.rectangles.append(rect)
        return len(self.rectangles) - 1  # 返回矩形框索引

    def update_rectangle(self, index, x1, y1, x2, y2):
        # 更新已存在的矩形框位置
        if 0 <= index < len(self.rectangles):
            self.canvas.coords(self.rectangles[index], x1, y1, x2, y2)

    def clear(self):
        # 清除所有矩形框
        for rect in self.rectangles:
            self.canvas.delete(rect)
        self.rectangles.clear()


# 畫框用的透明窗口
def create_overlay_window(x1, y1, x2, y2):
    overlay = tk.Toplevel()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-topmost", True)
    overlay.attributes("-alpha", 0.5)  # 透明度
    overlay.attributes("-transparentcolor", "black")  # 透明背景顏色
    overlay.configure(background="black")
    # 移除工作列圖示
    overlay.overrideredirect(True)
    canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # 繪製矩形框
    canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=1)
    # hwnd = int(overlay.winfo_id())
    # set_window_exclude(hwnd)  # 設置滑鼠穿透
    return overlay


my = php.kit()
pwd = os.path.dirname(os.path.realpath(sys.argv[0]))  # 取得 exe 檔案的目錄路徑
if my.is_dir(pwd + my.SP() + "data") == False:
    my.mkdir(pwd + my.SP() + "data")
    # os.chmod(pwd + my.SP() + "data", 0o777)
    os.chmod(pwd + my.SP() + "data", stat.S_IREAD | stat.S_IWRITE)
if my.is_dir(pwd + my.SP() + "data" + my.SP() + "projects") == False:
    my.mkdir(pwd + my.SP() + "data" + my.SP() + "projects")
    # os.chmod(pwd + my.SP() + "data" + my.SP() + "projects", 0o777)
    os.chmod(
        pwd + my.SP() + "data" + my.SP() + "projects", stat.S_IREAD | stat.S_IWRITE
    )

GDATA = {
    "VERSION": "0.01",
    "UI": {},
    "THREAD": {},
    "pwd": pwd,
    "recording": False,  # 錄製狀態
    "out": None,
    "record_area": None,
    "x1": 0,
    "xy": 0,
    "x2": 0,
    "y2": 0,
    "rect": None,
    "frame_list": [],  # 幀列表
    "run_start_time": None,  # 影片開始轉檔時間
    "run_end_time": None,  # 影片結束轉檔時間
}

lock_file = pwd + "\\lock.txt"

# 檢查是否存在鎖定檔案並創建文件鎖
# 防程式重複啟動
check_file_run = open(lock_file, "a+")
try:
    portalocker.lock(check_file_run, portalocker.LOCK_EX | portalocker.LOCK_NB)
except:
    messagebox.showinfo("說明", "程式已執行了...")
    sys.exit()


MESSAGE = """
我的 yolo 訓練機

版本: %s
作者: 羽山 (https://3wa.tw)  
    
""" % (
    GDATA["VERSION"]
)
icon_b64 = "AAABAAEAWFgAAAEAIABIfQAAFgAAACgAAABYAAAAsAAAAAEAIAAAAAAAAHkAAMEOAADBDgAAAAAAAAAAAAD/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////vOGs/6TXj/+k14//pNeP/6TXj/+k14//pNeP/7Ddnf//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////0evG/4zMcP+T0Hn//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7zhrP+T0Hn/dMNT/1+5Of9fuTn/a75I///////////////////////R68b/vOGs//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9Hrxv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of/R68b/////////////////pNeP/1+5Of9juz3/cMBO/4bKaf+T0Hn/0evG/////////////////////////////////////////////////6TXj///////////////////////////////////////////////////////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////dMNT/1+5Of9fuTn/X7k5/1+5Of9fuTn/nNSF/////////////////6TXj/9fuTn/X7k5/1+5Of9fuTn/X7k5/6TXj////////////////////////////////////////////6TXj/9fuTn/gMdi/////////////////////////////////////////////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/////////////////////////////////////////////////sN2d/4DHYv///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////5PQef9fuTn/X7k5/1+5Of9fuTn/X7k5/4bKaf////////////////+k14//X7k5/1+5Of9fuTn/X7k5/1+5Of/R68b//////////////////////////////////////9Hrxv9nvUP/X7k5/1+5Of9wwE7/0evG//////////////////////////////////////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO////////////////////////////////////////////sN2d/2O7Pf9fuTn/k9B5//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+84az/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/////////////////jMxw/1+5Of9fuTn/X7k5/1+5Of9fuTn///////////+T0Hn/gMdi/6TXj/////////////////96xVr/X7k5/1+5Of9fuTn/X7k5/2u+SP/R68b/////////////////////////////////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////////////////////////////////////sN2d/2O7Pf9fuTn/X7k5/1+5Of+w3Z3//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////2O7Pf9fuTn/X7k5/1+5Of9fuTn/Y7s9/////////////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5////////////dMNT/1+5Of9fuTn/Y7s9/3rFWv+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/a75I/9Hrxv///////////////////////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/////////////////////////////////0evG/2u+SP9fuTn/X7k5/1+5Of9fuTn/Y7s9/7Ddnf////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of+84az///////////+Gymn/X7k5/1+5Of9fuTn/X7k5/2u+SP///////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9rvkj/0evG//////////////////////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9juz3/sN2d////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP////////////esVa/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP/R68b/////////////////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv///////////////////////////4DHYv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2e9Q//R68b//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////5PQef9fuTn/X7k5/1+5Of9fuTn/X7k5/4zMcP///////////3DATv9fuTn/X7k5/1+5Of9fuTn/dMNT//////+w3Z3/X7k5/1+5Of9fuTn/X7k5/1+5Of+Ax2L/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7//////////////////////5zUhf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP+84az///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+k14//X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn///////////9wwE7/X7k5/1+5Of9fuTn/X7k5/4bKaf//////k9B5/1+5Of9fuTn/X7k5/1+5Of9juz3//////7Ddnf9juz3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of96xVr///////////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////7zhrP9juz3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3TDU//R68b/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////vOGs/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO////////////Y7s9/1+5Of9fuTn/X7k5/1+5Of+Gymn//////4DHYv9fuTn/X7k5/1+5Of9fuTn/dMNT////////////0evG/2u+SP9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/5PQef//////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv////////////////9rvkj/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3rFWv////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv///////////1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP//////9rvkj/X7k5/1+5Of9fuTn/X7k5/4zMcP/////////////////R68b/a75I/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9juz3/vOGs/4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3rFWv//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////a75I/1+5Of9fuTn/X7k5/1+5Of9fuTn//////7zhrP9fuTn/X7k5/1+5Of9fuTn/X7k5/6TXj///////X7k5/1+5Of9fuTn/X7k5/1+5Of+w3Z3//////////////////////9Hrxv9rvkj/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO//////+w3Z3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3rFWv///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5//////+k14//X7k5/1+5Of9fuTn/X7k5/1+5Of//////pNeP/1+5Of9fuTn/X7k5/1+5Of9juz3/////////////////////////////////0evG/2u+SP9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/Y7s9/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////a75I/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3rFWv////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of+84az/nNSF/1+5Of9fuTn/X7k5/1+5Of9fuTn//////4bKaf9fuTn/X7k5/1+5Of9fuTn/dMNT///////////////////////////////////////R68b/Y7s9/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/jMxw/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP/R68b/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////hspp/1+5Of9fuTn/X7k5/2e9Q/9wwE7/vOGs/5PQef9rvkj/X7k5/1+5Of9fuTn/cMBO//////9wwE7/X7k5/1+5Of9fuTn/X7k5/4zMcP///////////////////////////////////////////7Ddnf9juz3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/Z71D/2O7Pf9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP/R68b//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////6TXj/+c1IX/pNeP//////////////////////////////////////+w3Z3/k9B5/5PQef/R68b/X7k5/1+5Of9fuTn/X7k5/1+5Of+84az/////////////////////////////////////////////////k9B5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2O7Pf+w3Z3////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////R68b//////////////////////////////////////////////////////////////////////7zhrP+T0Hn/a75I/2O7Pf9nvUP///////////////////////////////////////////////////////////90w1P/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+k14/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////R68b/X7k5/3TDU/+MzHD/pNeP/////////////////////////////////////////////////////////////////2u+SP9nvUP/cMBO/7Ddnf//////////////////////////////////////////////////////0evG/2O7Pf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////k9B5/1+5Of9fuTn/X7k5/1+5Of9fuTn/a75I/3TDU/+Gymn/pNeP/7Ddnf////////////////////////////////9fuTn/X7k5/1+5Of9fuTn/Z71D/3rFWv////////////////////////////////////////////////+c1IX/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3TDU/9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP90w1P/hspp/5PQef+c1IX/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9Hrxv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/esVa/3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+T0Hn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/4zMcP9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////a75I/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+k14//cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3rFWv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn//////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////sN2d/2O7Pf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/Z71D/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO//////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+w3Z3/Y7s9/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2u+SP//////0evG/6TXj/+c1IX/hspp/3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/4bKaf//////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP////////////sN2d/7zhrP///////////6TXj/9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of////////////////+c1IX/sN2d////////////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7Ddnf9juz3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/esVa//////////////////////96xVr/X7k5/1+5Of9fuTn/X7k5/1+5Of+w3Z3//////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/6TXj////////////4DHYv9fuTn/a75I/4bKaf+T0Hn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/sN2d/3TDU/9fuTn/X7k5/3DATv///////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////nNSF/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+MzHD/////////////////Z71D/1+5Of9fuTn/X7k5/1+5Of9juz3///////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of+k14////////////9rvkj/X7k5/1+5Of9fuTn/gMdi/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/9Hrxv9juz3/X7k5/1+5Of9fuTn/pNeP//////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/7Ddnf//////vOGs/1+5Of9fuTn/X7k5/1+5Of9fuTn/dMNT////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP///////R68b/X7k5/1+5Of9fuTn/X7k5/5zUhf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of//////esVa/1+5Of9fuTn/X7k5/3rFWv//////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3TDU/9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9nvUP/0evG/4zMcP9fuTn/X7k5/1+5Of9fuTn/X7k5/5PQef///////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/6TXj///////k9B5/1+5Of9fuTn/X7k5/2u+SP+k14//X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn//////5zUhf9fuTn/X7k5/1+5Of9fuTn/vOGs/4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////R68b/Y7s9/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3TDU/+MzHD/Y7s9/1+5Of9fuTn/X7k5/1+5Of/R68b///////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of+k14///////3TDU/9fuTn/X7k5/1+5Of+MzHD/pNeP/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5////////////Z71D/1+5Of9fuTn/X7k5/4bKaf+Gymn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7Ddnf/R68b//////////////////////6TXj/9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/k9B5//////+w3Z3/jMxw/3TDU/96xVr/////////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP/9Hrxv9fuTn/X7k5/1+5Of9fuTn/vOGs/6TXj/9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of///////////3rFWv9fuTn/X7k5/1+5Of9juz3/gMdi/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+Ax2L/X7k5/2u+SP+Ax2L/jMxw/6TXj/+w3Z3/gMdi/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2O7Pf+84az//////////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/6TXj/+MzHD/X7k5/1+5Of9fuTn/cMBO//////+k14//X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn///////////+c1IX/X7k5/1+5Of9fuTn/X7k5/2e9Q/9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////Z71D/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/a75I//////////////////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of+k14//hspp/2e9Q/9fuTn/X7k5/6TXj///////pNeP/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/////////////////1+5Of9fuTn/a75I/4bKaf96xVr/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////pNeP/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn/////////////////////////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP////////////vOGs/4zMcP///////////6TXj/9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of////////////////+k14//0evG////////////hspp/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3rFWv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/7Ddnf///////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9Hrxv9juz3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9rvkj///////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+T0Hn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/4zMcP//////////////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////4zMcP9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9juz3/0evG/////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////k9B5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2O7Pf+c1IX/k9B5/4bKaf+Ax2L/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3rFWv////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////90w1P/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/gMdi/////////////////3rFWv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/pNeP////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////0evG/2O7Pf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+k14////////////+84az/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv////////////////////////////////////////////////////////////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/hspp//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+T0Hn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/a75I/////////////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/nNSF////////////////////////////////////////////////////////////////////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/4bKaf///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+MzHD////////////R68b/Y7s9/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/2e9Q////////////////////////////////////////////////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+w3Z3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/Y7s9/9Hrxv///////////4bKaf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9nvUP/a75I/3DATv9wwE7/cMBO/3DATv9wwE7/cMBO/3DATv9wwE7/cMBO/3DATv9wwE7/cMBO/3DATv9juz3/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/Z71D/3DATv9wwE7/cMBO/3DATv9wwE7/cMBO/3DATv9wwE7/cMBO/3DATv9wwE7/cMBO/3DATv+Ax2L//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3rFWv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of96xVr////////////R68b/Y7s9/1+5Of9fuTn/X7k5/1+5Of+Gymn/0evG/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+84az/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/7zhrP///////////4bKaf9fuTn/X7k5/3DATv+84az///////////9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3rFWv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of96xVr////////////R68b/a75I/5zUhf//////////////////////X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+84az/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/6TXj////////////////////////////////////////////1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/cMBO/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////3rFWv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7///////////////////////////////////////////9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/3DATv////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+k14//X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/7Ddnf//////////////////////////////////////X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of9wwE7//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////2u+SP9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of96xVr/////////////////////////////////////////////////////////////////////////////////////////////////////////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/4bKaf////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+T0Hn/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/7zhrP///////////////////////////////////////////////////////////////////////////////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////0evG/2O7Pf9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn///////////////////////////////////////////////////////////////////////////////////////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/hspp//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////96xVr/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/a75I////////////////////////////////////////////////////////////////////////////////////////////////////////////cMBO/1+5Of9fuTn/X7k5/1+5Of9fuTn/X7k5/4bKaf//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////sN2d/1+5Of9fuTn/X7k5/1+5Of90w1P/nNSF/////////////////////////////////////////////////////////////////////////////////////////////////////////////////3DATv9fuTn/X7k5/1+5Of9fuTn/X7k5/1+5Of+Gymn///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9nvUP/Z71D/4bKaf+84az///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9wwE7/X7k5/1+5Of9fuTn/X7k5/1+5Of9fuTn/hspp////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////sN2d////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def select_area_for_model():
    # 選擇訓練畫面範圍
    global GDATA
    if "overlay_model" in GDATA and GDATA["overlay_model"] != None:
        GDATA["overlay_model"].destroy()
        GDATA["overlay_model"] = None
    GDATA["record_area_model"] = tk.Toplevel()
    GDATA["record_area_model"].attributes("-fullscreen", True)
    GDATA["record_area_model"].attributes("-topmost", True)  # 確保在最上層
    GDATA["record_area_model"].configure(background="black")
    GDATA["record_area_model"].attributes("-alpha", 0.3)

    instruction = tk.Label(
        GDATA["record_area_model"], text="用滑鼠框選畫面範圍", bg="white"
    )
    instruction.pack()

    canvas = tk.Canvas(GDATA["record_area_model"], cursor="cross", bg="black")
    canvas.pack(fill="both", expand=True)

    GDATA["rect_model"] = None

    def on_button_press(event):
        global GDATA
        GDATA["x1_model"], GDATA["y1_model"] = event.x, event.y
        GDATA["rect_model"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red"
        )

    def on_move_press(event):
        global GDATA
        GDATA["x2_model"], GDATA["y2_model"] = event.x, event.y
        canvas.coords(
            GDATA["rect_model"],
            GDATA["x1_model"],
            GDATA["y1_model"],
            GDATA["x2_model"],
            GDATA["y2_model"],
        )

    def on_button_release(event):
        GDATA["record_area_model"].grab_release()  # 釋放滑鼠事件
        GDATA["record_area_model"].destroy()
        # hwnd = int(GDATA["record_area"].winfo_id())  # 獲取窗口句柄
        # set_window_exclude(hwnd)  # 設置穿透
        # GDATA["record_area"].attributes("-alpha", 0.1)  # 隱藏背景
        # canvas.unbind("<ButtonPress-1>")
        # canvas.unbind("<B1-Motion>")
        # canvas.unbind("<ButtonRelease-1>")
        # 儲存框選範圍
        x1, y1, x2, y2 = (
            GDATA["x1_model"],
            GDATA["y1_model"] + 22,
            event.x,
            event.y + 22,
        )

        GDATA["x1_model"], GDATA["y1_model"], GDATA["x2_model"], GDATA["y2_model"] = (
            x1,
            y1,
            x2,
            y2,
        )

        # 建立透明窗口繪製細框
        GDATA["overlay_model"] = create_overlay_window(x1, y1, x2, y2)

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)

    # GDATA["record_area_model"].grab_set_global()  # 捕獲滑鼠事件


def select_area():
    global GDATA
    if "overlay" in GDATA and GDATA["overlay"] != None:
        GDATA["overlay"].destroy()
        GDATA["overlay"] = None
    GDATA["record_area"] = tk.Toplevel()
    GDATA["record_area"].attributes("-fullscreen", True)
    GDATA["record_area"].attributes("-topmost", True)  # 確保在最上層
    GDATA["record_area"].configure(background="black")
    GDATA["record_area"].attributes("-alpha", 0.3)

    instruction = tk.Label(
        GDATA["record_area"], text="用滑鼠框選訓練畫面範圍", bg="white"
    )
    instruction.pack()

    canvas = tk.Canvas(GDATA["record_area"], cursor="cross", bg="black")
    canvas.pack(fill="both", expand=True)

    GDATA["rect"] = None

    def on_button_press(event):
        global GDATA
        GDATA["x1"], GDATA["y1"] = event.x, event.y
        GDATA["rect"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red"
        )

    def on_move_press(event):
        global GDATA
        GDATA["x2"], GDATA["y2"] = event.x, event.y
        canvas.coords(GDATA["rect"], GDATA["x1"], GDATA["y1"], GDATA["x2"], GDATA["y2"])

    def on_button_release(event):
        GDATA["record_area"].grab_release()  # 釋放滑鼠事件
        GDATA["record_area"].destroy()
        # hwnd = int(GDATA["record_area"].winfo_id())  # 獲取窗口句柄
        # set_window_exclude(hwnd)  # 設置穿透
        # GDATA["record_area"].attributes("-alpha", 0.1)  # 隱藏背景
        # canvas.unbind("<ButtonPress-1>")
        # canvas.unbind("<B1-Motion>")
        # canvas.unbind("<ButtonRelease-1>")
        # 儲存框選範圍
        x1, y1, x2, y2 = GDATA["x1"], GDATA["y1"] + 22, event.x, event.y + 22

        GDATA["x1"], GDATA["y1"], GDATA["x2"], GDATA["y2"] = x1, y1, x2, y2

        # 建立透明窗口繪製細框
        GDATA["overlay"] = create_overlay_window(x1, y1, x2, y2)

        # 儲存框選範圍到專案檔 rect.txt
        _OUTPUT_RECT_FILE = os.path.join(GDATA["project_folder"], "rect.txt")
        my.file_put_contents(
            _OUTPUT_RECT_FILE,
            my.json_encode({"x1": x1, "y1": y1, "x2": x2, "y2": y2}).encode("UTF-8"),
        )

        GDATA["UI"]["start_button"].config(state=tk.NORMAL)  # 啟用開始按鈕
        GDATA["UI"]["show_hide_rect_button"].config(state=tk.NORMAL)  # 啟用開始按鈕
        # 按鈕加紅邊框
        if GDATA["UI"]["show_hide_rect_button"].cget("text") == "隱藏圖框":
            GDATA["UI"]["show_hide_rect_button"].config(highlightcolor="red")

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)

    GDATA["record_area"].grab_set_global()  # 捕獲滑鼠事件


def method_count_wait_process_files():
    # 計算有多少待處理的檔案
    global GDATA
    GDATA["wait_process_files"] = 0
    fp = my.glob(GDATA["project_folder"] + my.SP() + "*.jpg")
    GDATA["wait_process_files"] = len(fp)
    GDATA["UI"]["status_label"].config(
        text="待處理檔案數：%s" % GDATA["wait_process_files"]
    )


def start_cut_screen():
    # 用 mss 截一張圖，放到 project_folder，檔名是 {t}.jpg
    global GDATA

    # 檢查是否有選擇範圍
    # 原本可能是 0 or None
    if GDATA["x1"] == GDATA["x2"] or GDATA["y1"] == GDATA["y2"]:
        # messagebox.showwarning("警告", "請先選擇拍照範圍！")
        print("請先選擇專案，或先選擇拍照範圍！")
        return

    # Lock UI
    t = str(int(my.microtime(True) * 1000.0))
    # print(my.microtime())
    GDATA["cut_screen_file"] = os.path.join(GDATA["project_folder"], t + ".jpg")
    sct = mss.mss(with_cursor=False)
    # monitor 為 GDATA 的 x1 ,x2, y1, y2

    monitor = {
        "left": GDATA["x1"],
        "top": GDATA["y1"],
        "width": GDATA["x2"] - GDATA["x1"],
        "height": GDATA["y2"] - GDATA["y1"],
    }

    # 藏掉細框
    # 有label == "隱藏圖框"，就是要隱藏，截完再後顯示
    NEED_SWITCH_RECT = False
    if (
        GDATA["UI"]["show_hide_rect_button"].cget("text") == "隱藏圖框"
        and "overlay" in GDATA
        and GDATA["overlay"] != None
    ):
        NEED_SWITCH_RECT = True

    if NEED_SWITCH_RECT == True:  # 截之前先隱藏
        do_show_hide_rect_button(False)

    frame = sct.grab(monitor)  # 截圖

    if NEED_SWITCH_RECT == True:  # 截完再後顯示
        do_show_hide_rect_button(True)
    mss.tools.to_png(frame.rgb, frame.size, output=GDATA["cut_screen_file"])
    # sct.shot(output=GDATA["cut_screen_file"])

    method_count_wait_process_files()


"""
def start_recording():
    global GDATA
    # Lock UI
    ui_enable_disable(False)

    t = str(int(time.time()))

    print("x1, y1: %s, %s" % (GDATA["x1"], GDATA["y1"]))
    print("x2, y2: %s, %s" % (GDATA["x2"], GDATA["y2"]))
    if GDATA["recording"]:
        messagebox.showwarning("警告", "錄影已經在進行中！")
        return
    if GDATA["x1"] == GDATA["x2"] or GDATA["y1"] == GDATA["y2"]:
        messagebox.showwarning("警告", "請先選擇拍照範圍！")
        return
    GDATA["UI"]["progress_label"].config(text="影像截取中...")
    GDATA["recording"] = True

    w = GDATA["x2"] - GDATA["x1"]
    h = GDATA["y2"] - GDATA["y1"]
    # GDATA["out"] = cv2.VideoWriter(GDATA["video_file"], cv2.VideoWriter_fourcc(*"MP4V"), GDATA["fps"], (w, h))
    GDATA["frame_list"] = []
    GDATA["THREAD"]["video_thread"] = threading.Thread(target=record_video)
    GDATA["THREAD"]["process_thread"] = threading.Thread(target=process_frames)

    GDATA["THREAD"]["video_thread"].start()
    GDATA["THREAD"]["process_thread"].start()

    GDATA["UI"]["start_button"].config(state=tk.DISABLED)
    GDATA["UI"]["stop_button"].config(state=tk.NORMAL)
"""


def ui_enable_disable(bool_val):
    global GDATA
    if bool_val == True:
        GDATA["UI"]["select_area_button"].config(state=tk.NORMAL)
        GDATA["UI"]["compression_level_selected_menu"].config(state=tk.NORMAL)
        GDATA["UI"]["exit_button"].config(state=tk.NORMAL)
    else:
        GDATA["UI"]["select_area_button"].config(state=tk.DISABLED)
        GDATA["UI"]["compression_level_selected_menu"].config(state=tk.DISABLED)
        GDATA["UI"]["exit_button"].config(state=tk.DISABLED)


def process_frames():
    global GDATA
    w = GDATA["x2"] - GDATA["x1"]
    h = GDATA["y2"] - GDATA["y1"]
    GDATA["out"] = cv2.VideoWriter(
        GDATA["video_file"], cv2.VideoWriter_fourcc(*"MP4V"), GDATA["fps"], (w, h)
    )
    last_frame_time = None

    # 每一幀間隔時間
    frame_step_time = 1 / GDATA["fps"]

    while GDATA["recording"] or len(GDATA["frame_list"]) > 0:
        if len(GDATA["frame_list"]) > 0:
            current_frame_data = GDATA["frame_list"].pop(0)
            current_time = current_frame_data["timestamp"]
            current_frame = current_frame_data["frame"]

            if last_frame_time is None:
                # 第一幀
                last_frame_time = current_time
                frame_rgb = cv2.cvtColor(np.array(current_frame), cv2.COLOR_RGBA2RGB)
                GDATA["out"].write(frame_rgb)
            else:
                # 計算時間差
                time_diff = current_time - last_frame_time
                if time_diff < frame_step_time:
                    # 超速了 這張多截的，不要
                    continue
                else:
                    # 按照時間差計算需要插入的幀數
                    # 用 int 取代 math.floor
                    frame_times = int(time_diff / frame_step_time)
                    for _ in range(frame_times):
                        frame_rgb = cv2.cvtColor(
                            np.array(current_frame), cv2.COLOR_RGBA2RGB
                        )
                        GDATA["out"].write(frame_rgb)
                    last_frame_time += (
                        frame_times * frame_step_time
                    )  # 更新最後一幀的時間
        time.sleep(0.001)  # 避免空循環佔用太多 CPU

    GDATA["out"].release()
    cv2.destroyAllWindows()


def record_video():
    global GDATA
    w = GDATA["x2"] - GDATA["x1"]
    h = GDATA["y2"] - GDATA["y1"]
    # 設置屏幕捕獲
    monitor = {"top": GDATA["y1"], "left": GDATA["x1"], "width": w, "height": h}
    # 幀時間間隔
    frame_time = 1 / GDATA["fps"]

    # 畫質
    _compression_level = GDATA["UI"]["compression_level_selected"].get()

    GDATA["frame_count"] = 0
    GDATA["run_start_time"] = time.time()
    GDATA["start_time"] = time.time()

    sct = mss.mss(compression_level=_compression_level, with_cursor=False)
    while GDATA["recording"]:
        # if is_need_cursor == True:
        #    # 這樣才會一直更新滑鼠位置
        #    # 後來直接改 mss/windows.py #328 與 #329 #367 的地方
        #    # mss/base.py #240~#243 回收 ram
        #    # 一直重新宣告 sct 造成記憶體肥大 crash
        #    sct = mss.mss(compression_level=_compression_level,with_cursor=is_need_cursor)
        # 記錄當前時間
        GDATA["frame_count"] += 1
        ct = time.time()
        elapsed_time = ct - GDATA["start_time"]

        # 截取指定區域的圖像
        try:
            GDATA["frame_list"].append({"timestamp": ct, "frame": sct.grab(monitor)})
        except:
            pass
        if elapsed_time >= 1.0:
            current_fps = GDATA["frame_count"] / elapsed_time
            GDATA["frame_count"] = 0
            GDATA["start_time"] = time.time()

    # out.release()
    # cv2.destroyAllWindows()


"""
def stop_recording():
    global GDATA

    if not GDATA["recording"]:
        messagebox.showwarning("警告", "錄影未開始！")
        return
    # Hide fps
    GDATA["UI"]["fps_label"].set("")
    GDATA["recording"] = False
    ui_enable_disable(True)

    # 影片最後才結束
    # time.sleep(3);
    GDATA["THREAD"]["video_thread"].join()
    GDATA["THREAD"]["process_thread"].join()
    GDATA["UI"]["start_button"].config(state=tk.NORMAL)
    GDATA["UI"]["stop_button"].config(state=tk.DISABLED)
    messagebox.showinfo("提示", "錄影已停止")
"""


def open_folder():
    global GDATA
    # 進到 projects 的專案裡
    if "project_folder" not in GDATA:
        # alert 請先選擇專案
        messagebox.showwarning("警告", "請先選擇專案檔！")
        return
    folder_path = GDATA["project_folder"]
    print(folder_path)
    webbrowser.open(folder_path)


def browser_folder():
    # 用瀏覽器開啟 http://localhost:9487
    global GDATA
    webbrowser.open(
        "http://localhost:9487/?project_name=" + my.urlencode(GDATA["project"])
    )


def on_message():
    global MESSAGE
    messagebox.showinfo("說明", MESSAGE)


def on_closing():
    global GDATA
    if GDATA["recording"]:
        if messagebox.askokcancel("離開", "錄影正在進行，確定要離開嗎？"):
            stop_recording()
            root.destroy()
            os._exit(1)
    else:
        root.destroy()
        os._exit(1)


# 函數：鼠標按下時的位置
def win_start_move(event):
    root.x = event.x
    root.y = event.y


def win_stop_move(event):
    root.x = None
    root.y = None


def win_do_move(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")


def project_get_list_all():
    # 取得所有專案檔
    global GDATA
    project_list = []
    for project in os.listdir(GDATA["pwd"] + "\\data\\projects"):
        if os.path.isdir(GDATA["pwd"] + "\\data\\projects\\" + project):
            project_list.append(project)
    return project_list


def new_project():
    # 新增專案檔
    # 會出現 prompt 讓使用者輸入專案檔名稱
    global GDATA
    project_name = simpledialog.askstring("新增專案檔", "請輸入專案檔名稱")
    if project_name is None:
        return
    if project_name == "":
        messagebox.showwarning("警告", "專案檔名稱不可為空！")
        return
    if project_name in project_get_list_all():
        messagebox.showwarning("警告", "專案檔名稱已存在！")
        return
    my.mkdir(
        GDATA["pwd"] + my.SP() + "data" + my.SP() + "projects" + my.SP() + project_name
    )
    os.chmod(
        GDATA["pwd"] + my.SP() + "data" + my.SP() + "projects" + my.SP() + project_name,
        stat.S_IREAD | stat.S_IWRITE,
    )  # 0o777
    # 繼續建立 dataset 與 my_dataset
    my.mkdir(
        GDATA["pwd"]
        + my.SP()
        + "data"
        + my.SP()
        + "projects"
        + my.SP()
        + project_name
        + my.SP()
        + "dataset"
    )
    os.chmod(
        GDATA["pwd"]
        + my.SP()
        + "data"
        + my.SP()
        + "projects"
        + my.SP()
        + project_name
        + my.SP()
        + "dataset",
        stat.S_IREAD | stat.S_IWRITE,  # 0o777,
    )
    my.mkdir(
        GDATA["pwd"]
        + my.SP()
        + "data"
        + my.SP()
        + "projects"
        + my.SP()
        + project_name
        + my.SP()
        + "my_dataset"
    )
    os.chmod(
        GDATA["pwd"]
        + my.SP()
        + "data"
        + my.SP()
        + "projects"
        + my.SP()
        + project_name
        + my.SP()
        + "my_dataset",
        stat.S_IREAD | stat.S_IWRITE,  # 0o777,
    )
    messagebox.showinfo("提示", "新增專案檔成功！")

    # 更新下拉選單，重新取得專案檔列表 並且設定選擇的專案檔
    GDATA["UI"]["select_project_selected_menu"]["menu"].delete(0, "end")
    GDATA["UI"]["select_project_selected"].set("選擇專案檔")
    for project in project_get_list_all():
        GDATA["UI"]["select_project_selected_menu"]["menu"].add_command(
            label=project,
            command=tk._setit(GDATA["UI"]["select_project_selected"], project),
        )
        GDATA["UI"]["select_project_selected_menu"].pack(side=tk.LEFT, padx=5)
        GDATA["UI"]["select_area_button"].config(state=tk.NORMAL)
        method_count_wait_process_files()  # 計算有多少待處理的檔案


def do_show_hide_rect_button(b):
    # 顯示或隱藏細框
    global GDATA
    if GDATA["overlay"] == None:
        return
    if b == True:
        # GDATA["overlay"] 顯示
        # GDATA["overlay"].deiconify()
        GDATA["overlay"].attributes("-alpha", 0.5)
    else:
        # GDATA["overlay"].withdraw()
        GDATA["overlay"].attributes("-alpha", 0.0)


def method_show_hide_rect_button():
    # 顯示或隱藏細框
    global GDATA
    if GDATA["overlay"] == None:
        return
    if GDATA["overlay"].winfo_viewable():
        GDATA["overlay"].withdraw()
        # 調整 show_hide_rect_button 文字
        GDATA["UI"]["show_hide_rect_button"].config(text="顯示圖框")
        # 按鈕取消紅邊框
        GDATA["UI"]["show_hide_rect_button"].config(highlightcolor="SystemButtonFace")
    else:
        GDATA["overlay"].deiconify()
        # 調整 show_hide_rect_button 文字
        GDATA["UI"]["show_hide_rect_button"].config(text="隱藏圖框")
        # 按鈕加紅邊框
        GDATA["UI"]["show_hide_rect_button"].config(highlightcolor="red")


def project_selected(self, a, b):
    # 選到專案檔後，才能選擇拍照範圍
    global GDATA
    project = GDATA["UI"]["select_project_selected"].get()
    if project == "選擇專案檔":
        GDATA["UI"]["select_area_button"].config(state=tk.DISABLED)
        GDATA["UI"]["execute_folder_button"].config(state=tk.DISABLED)
        return
    GDATA["project"] = project  # 設定選擇的專案檔名稱
    GDATA["UI"]["select_area_button"].config(
        state=tk.NORMAL
    )  # 選到專案檔後，才能選擇拍照範圍
    GDATA["UI"]["execute_folder_button"].config(
        state=tk.NORMAL
    )  # 選到專案檔後，才能選擇 編輯訓練檔
    GDATA["project_folder"] = (
        GDATA["pwd"] + my.SP() + "data" + my.SP() + "projects" + my.SP() + project
    )
    # 檢查是否有 rect.txt
    _OUTPUT_RECT_FILE = os.path.join(GDATA["project_folder"], "rect.txt")

    # 有選就重置
    if "overlay" in GDATA and GDATA["overlay"] != None:
        GDATA["overlay"].destroy()
        GDATA["overlay"] = None

    if my.is_file(_OUTPUT_RECT_FILE):
        jd = my.json_decode(my.file_get_contents(_OUTPUT_RECT_FILE))
        GDATA["x1"], GDATA["y1"], GDATA["x2"], GDATA["y2"] = (
            int(jd["x1"]),
            int(jd["y1"]),
            int(jd["x2"]),
            int(jd["y2"]),
        )
        # 建立透明窗口繪製細框
        GDATA["overlay"] = create_overlay_window(
            GDATA["x1"], GDATA["y1"], GDATA["x2"], GDATA["y2"]
        )
        GDATA["UI"]["start_button"].config(state=tk.NORMAL)  # 啟用開始按鈕
        GDATA["UI"]["show_hide_rect_button"].config(state=tk.NORMAL)  # 啟用開始按鈕
        # 按鈕加紅邊框
        if GDATA["UI"]["show_hide_rect_button"].cget("text") == "隱藏圖框":
            GDATA["UI"]["show_hide_rect_button"].config(highlightcolor="red")
    # 計算有多少待處理的檔案
    method_count_wait_process_files()


root = tk.Tk()

# 將 base64 字符串解碼為二進制數據
binary_data = base64.b64decode(icon_b64)

# 釋放 ram
icon_b64 = None

# 將二進制數據寫入文件
with open(GDATA["pwd"] + "\\tmp_icon.ico", "wb") as f:
    f.write(binary_data)
binary_data = None


# 設置窗口圖標
root.iconbitmap(GDATA["pwd"] + "\\tmp_icon.ico")
if os.path.isfile(GDATA["pwd"] + "\\tmp_icon.ico"):
    os.remove(GDATA["pwd"] + "\\tmp_icon.ico")

# 計算窗口位置
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 420  # 假設窗口寬度為 420
window_height = 160  # 假設窗口高度為  160

# 計算窗口位置: 右下角150px，距離底部30%
x = screen_width - window_width - 150
y = int(screen_height * 0.7)

# 設置窗口位置和大小
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# 設置窗口不可縮放
root.resizable(False, False)

root.title(f"我的 yolo 訓練機 - V%s By 羽山秋人 (https://3wa.tw)" % (GDATA["VERSION"]))

# 使用Frame將按鈕排成一行
# 第一列
GDATA["UI"]["first_frame"] = tk.Frame(root)
GDATA["UI"]["first_frame"].pack(padx=5, pady=10, fill=tk.X)

GDATA["UI"]["exit_button"] = tk.Button(
    GDATA["UI"]["first_frame"], text="離開程式", command=on_closing
)
GDATA["UI"]["exit_button"].pack(side=tk.RIGHT, padx=5)

GDATA["UI"]["btn_desktop_example_button"] = tk.Button(
    GDATA["UI"]["first_frame"], text="桌面範例(已停止)", command=run_desktop_example
)
GDATA["UI"]["btn_desktop_example_button"].pack(side=tk.RIGHT, padx=5)

GDATA["UI"]["info_button"] = tk.Button(
    GDATA["UI"]["first_frame"], text="說明", command=on_message
)
GDATA["UI"]["info_button"].pack(side=tk.RIGHT, padx=5)


# 以下放到第二行
# 第二列

GDATA["UI"]["second_frame"] = tk.Frame(root)
GDATA["UI"]["second_frame"].pack(padx=5, fill=tk.X)

# 新增專案檔，按到會出現 prompt 讓使用者輸入專案檔名稱
GDATA["UI"]["new_project_button"] = tk.Button(
    GDATA["UI"]["second_frame"], text="新增專案檔", command=new_project
)
GDATA["UI"]["new_project_button"].pack(side=tk.LEFT, padx=5)

# 下拉選單，選擇專案檔
GDATA["UI"]["select_project_selected"] = tk.StringVar()
GDATA["UI"]["select_project_selected"].set("選擇專案檔")
GDATA["UI"]["select_project_selected_menu"] = tk.OptionMenu(
    GDATA["UI"]["second_frame"], GDATA["UI"]["select_project_selected"], "選擇專案檔"
)
# 更新下拉選單，重新取得專案檔列表 並且設定選擇的專案檔
GDATA["UI"]["select_project_selected_menu"]["menu"].delete(0, "end")
GDATA["UI"]["select_project_selected"].set("選擇專案檔")
for project in project_get_list_all():
    GDATA["UI"]["select_project_selected_menu"]["menu"].add_command(
        label=project,
        command=tk._setit(GDATA["UI"]["select_project_selected"], project),
    )
    GDATA["UI"]["select_project_selected_menu"].pack(side=tk.LEFT, padx=5)
    # GDATA["UI"]["select_area_button"].config(state=tk.NORMAL)
GDATA["UI"]["select_project_selected_menu"].pack(side=tk.LEFT, padx=5)
# 選到專案檔後，才能選擇拍照範圍
GDATA["UI"]["select_project_selected"].trace("w", project_selected)

GDATA["UI"]["execute_folder_button"] = tk.Button(
    GDATA["UI"]["second_frame"],
    text="編輯訓練檔",
    command=browser_folder,
    state=tk.DISABLED,
)
GDATA["UI"]["execute_folder_button"].pack(side=tk.LEFT, padx=5)

GDATA["UI"]["open_folder_button"] = tk.Button(
    GDATA["UI"]["second_frame"], text="資料夾", command=open_folder
)
GDATA["UI"]["open_folder_button"].pack(side=tk.LEFT, padx=5)


# 第三列
GDATA["UI"]["third_frame"] = tk.Frame(root)
GDATA["UI"]["third_frame"].pack(padx=5, pady=10, fill=tk.X)


# 選擇拍照範圍 必需有專案檔才能選擇
GDATA["UI"]["select_area_button"] = tk.Button(
    GDATA["UI"]["third_frame"],
    text="選擇拍照範圍",
    command=select_area,
    state=tk.DISABLED,
)
GDATA["UI"]["select_area_button"].pack(side=tk.LEFT, padx=5)

GDATA["UI"]["start_button"] = tk.Button(
    GDATA["UI"]["third_frame"],
    text="截圖(熱鍵)：CTRL + F2",
    command=start_cut_screen,
    state=tk.DISABLED,  # 選擇拍照範圍後才能截圖
)
GDATA["UI"]["start_button"].pack(side=tk.LEFT, padx=5)

GDATA["UI"]["show_hide_rect_button"] = tk.Button(
    GDATA["UI"]["third_frame"],
    text="隱藏圖框",
    command=method_show_hide_rect_button,
    highlightthickness=1,
    # fg="#ffffff",
    highlightcolor="SystemButtonFace",  #'SystemButtonFace',
    default="active",
    state=tk.DISABLED,  # 選擇拍照範圍後才能截圖
)
GDATA["UI"]["show_hide_rect_button"].pack(side=tk.LEFT, padx=5)


"""
GDATA["UI"]["stop_button"] = tk.Button(
    GDATA["UI"]["third_frame"],
    text="停止錄影",
    command=stop_recording,
    state=tk.DISABLED,
)
GDATA["UI"]["stop_button"].pack(side=tk.LEFT, padx=5)
"""


# 第四列，狀態列
GDATA["UI"]["fourth_frame"] = tk.Frame(root)
GDATA["UI"]["fourth_frame"].pack(padx=5, pady=5, fill=tk.X)

GDATA["UI"]["status_label"] = tk.Label(GDATA["UI"]["fourth_frame"], text="")
GDATA["UI"]["status_label"].pack(side=tk.LEFT, padx=5)


root.protocol("WM_DELETE_WINDOW", on_closing)


# 綁定標題欄的鼠標按下事件
root.bind("<ButtonPress-1>", win_start_move)
root.bind("<ButtonRelease-1>", win_stop_move)
root.bind("<B1-Motion>", win_do_move)


# 跑一個本地的 flask server port 9487
# 這樣就可以在網頁上看到 www/index.html 的畫面
# 程式開始
# 用 thread 跑
def run_flask():
    app = Flask(__name__, template_folder="www", static_folder="www")

    @app.route("/")
    def home():
        return render_template("index.html")

    # data 目錄也要分享
    @app.route("/data/<path:filename>")
    def data(filename):
        _PWD = os.getcwd()
        DATA_FOLDER = _PWD + my.SP() + "data"
        return send_from_directory(DATA_FOLDER, filename)

    @app.route("/api", methods=["GET", "POST"])
    def api():
        GETS = request.args
        if "mode" in GETS:
            mode = GETS["mode"]
            if mode == "project_list":
                _PWD = os.getcwd()
                projects = my.glob_dirs(
                    _PWD + my.SP() + "data" + my.SP() + "projects" + my.SP() + "*"
                )
                projects = [os.path.basename(p) for p in projects]
                return jsonify({"status": "OK", "data": projects})
            if mode == "getKindList":
                # 從 my_dataset 資料夾取得所有的類別
                # project_name 是 POST project_name

                if "project_name" not in request.form:
                    return (
                        jsonify({"status": "NO", "reason": "Missing project_name"}),
                        400,
                    )
                project_name = request.form["project_name"]
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _MY_DATASET_FOLDER = _PROJECT_FOLDER + my.SP() + "my_dataset"
                _KINDS = my.glob_dirs(_MY_DATASET_FOLDER + my.SP() + "*")
                OUTPUT = {"status": "OK", "data": {}}

                # 重要
                # 排序方向，依目錄的建立時間舊到新
                _KINDS = sorted(_KINDS, key=os.path.getctime)

                for kind in _KINDS:
                    _KIND = os.path.basename(kind)
                    _KIND_FILES = len(my.glob(kind + my.SP() + "*.jpg"))
                    OUTPUT["data"][_KIND] = {"數量": _KIND_FILES}

                return jsonify(OUTPUT)
            if mode == "addKind":
                # 新增類別
                # project_name 是 POST project_name
                # kind 是 POST kind
                if "project_name" not in request.form:
                    return (
                        jsonify({"status": "NO", "reason": "Missing project_name"}),
                        400,
                    )
                if "kind_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "請輸入類別名稱"})
                project_name = request.form["project_name"]
                kind_name = request.form["kind_name"]
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _MY_DATASET_FOLDER = _PROJECT_FOLDER + my.SP() + "my_dataset"
                _KIND_FOLDER = _MY_DATASET_FOLDER + my.SP() + kind_name
                my.mkdir(_KIND_FOLDER)
                os.chmod(_KIND_FOLDER, stat.S_IREAD | stat.S_IWRITE)  # 0o777
                if my.is_dir(_KIND_FOLDER):
                    return jsonify({"status": "OK"})
                else:
                    return jsonify(
                        {"status": "NO", "reason": "目錄不存在，未建立成功..."}
                    )
            if mode == "delKind":
                if "project_name" not in request.form:
                    return (
                        jsonify({"status": "NO", "reason": "Missing project_name"}),
                        400,
                    )
                if "kind_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "請輸入類別名稱"})
                project_name = request.form["project_name"]
                kind_name = my.basename(request.form["kind_name"])
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _MY_DATASET_FOLDER = _PROJECT_FOLDER + my.SP() + "my_dataset"
                _KIND_FOLDER = _MY_DATASET_FOLDER + my.SP() + kind_name
                print("Del path: %s" % (_KIND_FOLDER))
                # if my.is_dir(_KIND_FOLDER):
                my.delete_directory_contents(_KIND_FOLDER)
                return jsonify({"status": "OK"})
            if mode == "editKind":
                if "project_name" not in request.form:
                    return (
                        jsonify({"status": "NO", "reason": "Missing project_name"}),
                        400,
                    )
                if "kind_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "請輸入類別名稱"})
                if "new_kind_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "請輸入新類別名稱"})
                project_name = request.form["project_name"]
                kind_name = my.basename(request.form["kind_name"])
                new_kind_name = my.basename(request.form["new_kind_name"])
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _MY_DATASET_FOLDER = _PROJECT_FOLDER + my.SP() + "my_dataset"
                _KIND_FOLDER = _MY_DATASET_FOLDER + my.SP() + kind_name
                _NEW_KIND_FOLDER = _MY_DATASET_FOLDER + my.SP() + new_kind_name
                if (
                    my.is_dir(_KIND_FOLDER) == True
                    and my.is_dir(_NEW_KIND_FOLDER) == False
                ):
                    os.rename(_KIND_FOLDER, _NEW_KIND_FOLDER)
                elif my.is_dir(_KIND_FOLDER) == False:
                    return jsonify({"status": "NO", "reason": "類別不存在"})
                elif my.is_dir(_NEW_KIND_FOLDER) == True:
                    return jsonify({"status": "NO", "reason": "新類別已存在"})
                return jsonify({"status": "OK"})
            if mode == "getPhotoList":
                # 取得 project_name 目錄下的圖片，因為是未分類的
                project_name = request.form["project_name"]
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                fp = my.glob(_PROJECT_FOLDER + my.SP() + "*.jpg")
                fp = [{"photo_name": my.basename(f)} for f in fp]
                return jsonify({"status": "OK", "data": fp})
            # 刪照片
            if mode == "delPhoto":
                if "project_name" not in request.form:
                    return (
                        jsonify({"status": "NO", "reason": "沒有這個專案..."}),
                        400,
                    )
                if "photo_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "圖片名稱未填..."})
                project_name = request.form["project_name"]
                photo_name = my.basename(request.form["photo_name"])
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _PHOTO_FILE = _PROJECT_FOLDER + my.SP() + photo_name
                if my.is_file(_PHOTO_FILE):
                    os.remove(_PHOTO_FILE)
                    return jsonify({"status": "OK"})
                else:
                    return jsonify({"status": "NO", "reason": "圖片不存在"})
            if mode == "setPhotoToKind":
                # 把圖片放到類別裡

                project_name = request.form["project_name"]
                kind_name = request.form["kind_name"]
                photo_name = my.basename(request.form["photo_name"])
                if "project_name" not in request.form:
                    return (
                        jsonify({"status": "NO", "reason": "沒有這個專案..."}),
                        400,
                    )
                if "photo_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "圖片名稱未填..."})
                if "kind_name" not in request.form:
                    return jsonify({"status": "NO", "reason": "類別名稱未填..."})
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _MY_DATASET_FOLDER = _PROJECT_FOLDER + my.SP() + "my_dataset"
                _KIND_FOLDER = _MY_DATASET_FOLDER + my.SP() + kind_name
                _PHOTO_FILE = _PROJECT_FOLDER + my.SP() + photo_name
                _NEW_PHOTO_FILE = _KIND_FOLDER + my.SP() + photo_name
                if my.is_file(_PHOTO_FILE) == False:
                    return jsonify({"status": "NO", "reason": "圖片不存在"})
                if my.is_dir(_KIND_FOLDER) == False:
                    my.mkdir(_KIND_FOLDER)
                    os.chmod(_KIND_FOLDER, stat.S_IREAD | stat.S_IWRITE)
                if my.is_file(_NEW_PHOTO_FILE) == True:
                    my.unlink(_NEW_PHOTO_FILE)
                shutil.move(_PHOTO_FILE, _NEW_PHOTO_FILE)
                # 有移成功嗎
                if my.is_file(_NEW_PHOTO_FILE):
                    return jsonify({"status": "OK"})
                else:
                    return jsonify({"status": "NO", "reason": "移動失敗"})
            if mode == "getDoMarkKindList":
                # 取得 project_name 目錄下的圖片，已分類的照片數量、未處理的照片數量
                project_name = request.form["project_name"]
                _PWD = os.getcwd()
                _PROJECT_FOLDER = (
                    _PWD
                    + my.SP()
                    + "data"
                    + my.SP()
                    + "projects"
                    + my.SP()
                    + project_name
                )
                _MY_DATASET_FOLDER = _PROJECT_FOLDER + my.SP() + "my_dataset"
                _KINDS = my.glob_dirs(_MY_DATASET_FOLDER + my.SP() + "*")
                _data = []
                for kind in _KINDS:
                    _KIND = os.path.basename(kind)
                    _KIND_FILES = len(my.glob(kind + my.SP() + "*.jpg"))
                    _TXT_FILES = len(my.glob(kind + my.SP() + "*.txt"))
                    _data.append(
                        {
                            "kind_name": _KIND,
                            "total_pics": _KIND_FILES,
                            "need_process_counts": _KIND_FILES - _TXT_FILES,
                        }
                    )
                return jsonify({"status": "OK", "data": _data})
        return jsonify({"status": "OK"})

    @app.route("/datetime", methods=["GET", "POST"])
    def datetime():
        return my.date("Y-m-d H:i:s")

    @app.route("/test", methods=["GET", "POST"])
    def test():
        # 獲取 GET 或 POST 請求中的數據
        string_fields = request.args  # 對於 GET 請求
        if request.method == "POST":
            string_fields = request.form  # 對於 POST 請求

        output = {}
        for key in string_fields:
            output[key] = string_fields[key]

        return output

    app.run(debug=True, host="127.0.0.1", port=9487, threaded=True, use_reloader=False)


threading.Thread(target=run_flask).start()

# 註冊熱鍵 CTRL + ALT + ` 或 CTRL + ALT + ~，或 CTRL + ALT + F1
# keyboard.add_hotkey("ctrl+alt+~", start_cut_screen)  # 設置螢幕熱鍵
keyboard.add_hotkey("ctrl+f2", start_cut_screen)  # 設置螢幕熱鍵
# keyboard.add_hotkey('ctrl+alt+~', start_cut_screen)  # 設置螢幕熱鍵
# 創建 OverlayWindow 實例
overlay_window = OverlayWindow(root)

root.mainloop()
