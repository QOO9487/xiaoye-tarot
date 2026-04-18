import streamlit as st
import google.generativeai as genai

# 1. 網頁頁面標題與圖示
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：AI塔羅諮詢")

# 2. 從 Streamlit Secrets 讀取 API Key
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# 3. 占卜大師指令 (System Instruction)
instruction = """
你是一位具備資深背景與極高洞察力的塔羅占卜大師。語氣沉穩、睿智且專業。
[第一階段：確認身分] 第一句話必須且只能是：您好！請問我該如何稱呼你？
[第二階段：三牌校準] 要求對方提供三張牌名與正逆位，並做出性別與年齡判定。
[注意事項] 請使用台灣口吻，嚴禁使用「20代」等語法。
"""

# 4. 核心修復：自動嘗試多種模型名稱
@st.cache_resource
def load_tarot_master():
    # 按照穩定度排序的名稱清單
    possible_models = [
        "gemini-1.5-flash",         # 簡稱
        "models/gemini-1.5-flash",  # 全稱
        "gemini-pro",               # 備用方案
        "models/gemini-pro"         # 備用方案全稱
    ]
    
    for model_name in possible_models:
        try:
            m = genai.GenerativeModel(model_name=model_name, system_instruction=instruction)
            # 測試一下模型是否真的可用
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

model = load_tarot_master()

if model is None:
    st.error("❌ 系統初始化失敗：目前所有模型路徑皆無法連線，請檢查 API Key 權限。")
    st.stop()

# --- 5. 初始化對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    try:
        response = st.session_state.chat.send_message("請依照指令，發起第一階段的問候。")
        st.session_state.messages = [{"role": "assistant", "content": response.text}]
    except:
        st.session_state.messages = [{"role": "assistant", "content": "您好！請問我該如何稱呼你？"}]

# --- 6. 渲染畫面 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. 使用者輸入 ---
if prompt := st.chat_input("請輸入您的稱呼或占卜訊息...", key="main_chat"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("大師正在感應牌陣..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"連線異常：{e}")
