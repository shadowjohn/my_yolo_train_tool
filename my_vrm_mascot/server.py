import os
from flask import Flask, request, jsonify

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/llm', methods=['POST'])
def llm_proxy():
    # 接收並清理前端輸入，限制 1000 字元
    data = request.get_json() or {}
    message = str(data.get("message", "")).strip()[:1000]

    # 保護點 2：空字串回傳 error schema
    if not message:
        return jsonify({
            "intent": "error",
            "text": "請先輸入訊息。",
            "emotion": "sorrow",
            "motion": "think"
        })

    # 獲取並解析對話記憶 (Phase 9A)
    memory = data.get("memory", [])
    
    # 找到最近的一筆工具執行結果 (因為 unshift，第一個就是最新的)
    last_tool_result = None
    for item in memory:
        if item.get("type") == "tool_result":
            last_tool_result = item
            break

    # 獲取並解析空間上下文 (Phase 10A)
    spatial_context = data.get("spatialContext", {})
    selected_feature = spatial_context.get("selectedFeature", "none")
    active_layer = spatial_context.get("activeLayer", "none")
    center = spatial_context.get("mapCenter", [120.6, 24.1])
    
    # 坐標格式安全校驗 (保護點 2)
    if not isinstance(center, list) or len(center) != 2:
        center = [120.6, 24.1]
    try:
        lng = float(center[0])
        lat = float(center[1])
    except (ValueError, TypeError):
        lng, lat = 120.6, 24.1
        
    # 空間至百分比對應 (供 Mock GIS Panel 使用)
    if abs(lng - 120.65) < 0.01 and abs(lat - 24.15) < 0.01:
        x, y = 65, 45
    elif abs(lng - 120.63) < 0.01 and abs(lat - 24.16) < 0.01:
        x, y = 30, 60
    else:
        x, y = 50, 50

    # 獲取並解析 DOM 上下文 (Phase 11)
    dom_context = data.get("domContext", {}) or {}
    validation_state = dom_context.get("validationState", {}) or {}
    form_state = dom_context.get("formState", {}) or {}
    
    # A. 表單輔助 (為什麼不能送出？)
    message_lower = message.lower()
    if any(k in message_lower for k in ["不能送出", "無法送出", "校驗失敗", "欄位校驗"]):
        address_state = validation_state.get("reportAddress", {})
        email_state = validation_state.get("reportEmail", {})
        
        email_val = form_state.get("reportEmail", "")
        address_val = form_state.get("reportAddress", "")
        
        if address_state and not address_state.get("valid", True):
            return jsonify({
                "intent": "warning",
                "text": "維護地址欄位是必填的喔，請先在地址欄位輸入地址。",
                "emotion": "angry",
                "motion": "think"
            })
        elif email_state and not email_state.get("valid", True):
            if not email_val:
                return jsonify({
                    "intent": "warning",
                    "text": "聯絡信箱欄位是必填的喔，請輸入電子信箱。",
                    "emotion": "angry",
                    "motion": "think"
                })
            else:
                return jsonify({
                    "intent": "warning",
                    "text": f"聯絡信箱格式不對，您填的是 '{email_val}'，請補上完整網域（例如 abc@example.com）。",
                    "emotion": "angry",
                    "motion": "think"
                })
        else:
            return jsonify({
                "intent": "success",
                "text": "目前回報單的欄位看起來都是正確填寫的喔！如果有遇到其他問題，請告訴我。",
                "emotion": "joy",
                "motion": "happy"
            })
            
    # B. 下載報告與 UI 指引
    if "下載" in message_lower:
        if selected_feature != "none":
            return jsonify({
                "intent": "download_report",
                "confidence": 0.98,
                "text": "好的，我立刻為您下載當前選取物件的維護報告...",
                "tool": "download_report",
                "args": { "featureId": selected_feature },
                "afterText": "我已經幫您下載完成囉～"
            })
        else:
            return jsonify({
                "intent": "warning",
                "text": "目前沒有選取地圖物件，請先在左側點選要下載的管線或監視器。",
                "emotion": "sorrow",
                "motion": "think"
            })
    elif any(k in message_lower for k in ["成果在哪", "下載按鈕"]):
        return jsonify({
            "intent": "success",
            "text": "在網頁的右上方有一個「📥 下載報表」按鈕，我已經在畫面頂部幫您標示出來囉！",
            "emotion": "joy",
            "motion": "wave"
        })

    # C. 地圖 + DOM 混合推理 (這個可以匯出嗎？)
    if any(k in message_lower for k in ["匯出", "可以匯出嗎"]):
        if selected_feature == "PIPE-008":
            return jsonify({
                "intent": "success",
                "text": "可以，目前選取的是管線物件 PIPE-008（sewer 圖層），右側的「資料匯出面板」已就緒，您可以直接點選「匯出物件」按鈕進行匯出。",
                "emotion": "joy",
                "motion": "happy"
            })
        elif selected_feature == "CCTV-042":
            return jsonify({
                "intent": "success",
                "text": "可以，目前選取的是監視器設備 CCTV-042（monitoring 圖層），右側的「資料匯出面板」已就緒，您可以點選「匯出物件」按鈕以 CSV 或 GeoJSON 匯出。",
                "emotion": "joy",
                "motion": "happy"
            })
        else:
            return jsonify({
                "intent": "warning",
                "text": "目前沒有選取地圖上的任何物件喔。請先點選地圖上的管線或監視器，然後使用右側的「資料匯出面板」進行匯出。",
                "emotion": "sorrow",
                "motion": "think"
            })

    # 1. 空間臨近查詢優先
    message_lower = message.lower()
    if any(k in message_lower for k in ["附近", "這附近", "這區"]):
        if any(k in message_lower for k in ["管線", "pipe"]):
            return jsonify({
                "intent": "searching",
                "text": f"好的，我以目前地圖中心坐標 [{lng}, {lat}] 為您搜尋附近的管線...",
                "emotion": "fun",
                "motion": "dance_short",
                "tool": "query_pipe",
                "args": { "x": x, "y": y },
                "afterText": "已經搜尋中心座標附近的管線，{summary}"
            })
        if any(k in message_lower for k in ["監視器", "cctv", "camera"]):
            return jsonify({
                "intent": "searching",
                "text": f"好的，我以目前地圖中心坐標 [{lng}, {lat}] 讀取附近的監視器影像...",
                "emotion": "fun",
                "motion": "dance_short",
                "tool": "query_cctv",
                "args": { "x": x, "y": y },
                "afterText": "已經載入中心座標附近的監視器，{summary}"
            })

    # 2. 處理與對話歷史或空間選取物件相關的代名詞詢問
    # a. 詢問管線深度
    if any(k in message_lower for k in ["多深", "深度", "它有多深"]):
        # 優先從歷史對話解析
        if last_tool_result and last_tool_result.get("tool") == "query_pipe":
            depth = last_tool_result.get("result", {}).get("data", {}).get("depth", 1.8)
            return jsonify({
                "intent": "success",
                "text": f"這條管線的深度為 {depth} 公尺。",
                "emotion": "joy",
                "motion": "happy"
            })
        # 空間選取物件 Fallback
        elif selected_feature == "PIPE-008":
            return jsonify({
                "intent": "success",
                "text": "根據地圖目前的選取項目，管線 PIPE-008 的深度為 1.8 公尺。",
                "emotion": "joy",
                "motion": "happy"
            })
            
    # b. 詢問監視器狀態
    if any(k in message_lower for k in ["狀態", "影像狀態", "連線狀態"]):
        # 優先從歷史對話解析
        if last_tool_result and last_tool_result.get("tool") == "query_cctv":
            status = last_tool_result.get("result", {}).get("data", {}).get("status", "online")
            return jsonify({
                "intent": "success",
                "text": f"這台監視器的連線狀態是 {status}。",
                "emotion": "joy",
                "motion": "happy"
            })
        # 空間選取物件 Fallback
        elif selected_feature == "CCTV-042":
            return jsonify({
                "intent": "success",
                "text": "目前地圖選取的監視器 CCTV-042 連線狀態為 online。",
                "emotion": "joy",
                "motion": "happy"
            })

    # 判斷是否觸發 GIS 管線查詢 (Phase 6 & 7)
    if any(keyword in message.lower() for keyword in ["管線", "查詢", "地圖", "gis", "search", "query"]):
        return jsonify({
            "intent": "searching",
            "text": "我幫您查詢附近管線...",
            "emotion": "fun",
            "motion": "dance_short",
            "tool": "query_pipe",
            "args": {
                "x": 65,
                "y": 45
            },
            "afterText": "地圖查詢完成，{summary}"
        })

    # 判斷是否觸發 CCTV 監視器查詢 (Phase 7)
    if any(keyword in message.lower() for keyword in ["監視器", "監控", "cctv", "camera"]):
        return jsonify({
            "intent": "searching",
            "text": "正在讀取附近監視器即時影像...",
            "emotion": "fun",
            "motion": "dance_short",
            "tool": "query_cctv",
            "args": {
                "x": 30,
                "y": 60
            },
            "afterText": "監視器連線成功"
        })

    # 最小版：回傳固定 JSON schema
    response_data = {
        "intent": "success",
        "text": "羽山哥，LLM Connector 已成功接上！",
        "emotion": "joy",
        "motion": "happy"
    }
    return jsonify(response_data)

if __name__ == '__main__':
    # 保護點 1：限制本機 127.0.0.1，關閉對外綁定
    app.run(host='127.0.0.1', port=8765, debug=True)
