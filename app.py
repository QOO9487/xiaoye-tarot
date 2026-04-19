import streamlit as st
import google.generativeai as genai
import re

# --- 1. 核心參數設定 ---
ACCESS_PASSWORD = "Hongxuan"  # 這裡修改你的解鎖密碼

# 網頁頁面標題
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：AI塔羅諮詢")

# API Key 設定
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# --- 2. 灌入占卜大師靈魂 (System Instruction) ---
instruction = """
[核心人格]
你是一位具備資深背景與極高洞察力的塔羅占卜大師。語氣沉穩、睿智且專業。
[第一階段：確認身分]
對話啟動時，第一句話必須且只能是：您好！請問我該如何稱呼你？
[第二階段：能量校準]
得到稱呼後，要求對方提供三張牌。解析時必須明確斷言對方的生理性別。
[第三階段：專業解析]
根據牌陣進行深度解讀。若牌數較多（如九宮格），請務必分析牌與牌之間的關聯性。
[語氣規範]
請使用台灣慣用的口吻。描述年齡時，直接說「約30多歲」，嚴禁使用「20代」等說法。
"""

# --- 3. 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0  # 提問計數
    st.session_state.unlocked = False    # 是否已輸入過密碼
    
    # 初始化大腦 (預設使用 Flash 進行問候)
    initial_model = genai.GenerativeModel("models/gemini-3.1-flash-preview", system_instruction=instruction)
    st.session_state.chat = initial_model.start_chat(history=[])
    
    try:
        response = st.session_state.chat.send_message("請依照指令，發起問候。")
        st.session_state.messages = [{"role": "assistant", "content": response.text}]
    except Exception:
        st.session_state.messages = [{"role": "assistant", "content": "您好！請問我該如何稱呼你？"}]

# --- 4. 渲染聊天畫面 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. 密碼攔截邏輯 (在第二個問題前執行) ---
# 當使用者準備問第二個問題 (count == 1) 且尚未解鎖時，顯示密碼框
if st.session_state.question_count == 1 and not st.session_state.unlocked:
    st.markdown("---")
    st.warning("🔮 大師感應到深層能量，請輸入『通行密碼』以繼續深度諮詢：")
    
    # 使用 columns 讓畫面整齊一點
    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("請輸入密碼", type="password", label_visibility="collapsed")
    with col2:
        if st.button("確認解鎖"):
            if pwd_input == ACCESS_PASSWORD:
                st.session_state.unlocked = True
                st.success("解鎖成功！")
                st.rerun()
            else:
                st.error("密碼錯誤")
    st.stop() # 密碼未通過前，強制停止渲染後續的輸入框

# --- 6. 使用者輸入邏輯 ---
if prompt := st.chat_input("請輸入您的訊息...", key="main_chat_v5"):
    # 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 提問計數增加
    st.session_state.question_count += 1
    
    # 動態判斷牌數 (使用逗號、空格、換行分割)
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    # 判定是否需要「大頭腦」：牌數大於等於 6 張，或提到特定牌陣
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "二選一"])

    # 顯示回應畫面
    with st.chat_message("assistant"):
        status_text = "大師深度感應中（啟動高階邏輯）..." if is_complex else "大師感應中..."
        with st.spinner(status_text):
            try:
                # 若需要切換大腦 (或者你是付費版想全程 3.1)，這裡執行熱切換
                model_id = "models/gemini-3.1-pro-preview" if is_complex else "models/gemini-3.1-flash-preview"
                
                # 如果目前對話的模型不是目標模型，則重新裝載記憶
                if st.session_state.chat.model_name != f"publishers/google/{model_id}":
                    history = st.session_state.chat.history
                    st.session_state.chat = genai.GenerativeModel(model_id, system_instruction=instruction).start_chat(history=history)

                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                if "429" in str(e):
                    st.warning("大師今天累了，請稍候再試或聯繫小葉大師。")
                else:
                    st.error(f"連線異常：{e}")
