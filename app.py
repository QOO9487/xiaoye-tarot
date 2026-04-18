import streamlit as st
import google.generativeai as genai

# 網頁基本設定
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：專業塔羅諮詢")

# 設定 API Key
API_KEY = "AIzaSyAKkfy479-Itbg9LMFziX7pQr8YXq_3x28" # 使用你最新申請的那組
genai.configure(api_key=API_KEY)

# 占卜大師指令
instruction = """
[請完整貼入你原本的那段大師提示詞]
"""

# --- 核心修復點：嘗試多種模型名稱格式 ---
@st.cache_resource
def load_model():
    # 這裡列出目前最可能的正確路徑格式
    model_names = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-1.5-flash-latest"]
    for name in model_names:
        try:
            m = genai.GenerativeModel(model_name=name, system_instruction=instruction)
            # 測試一下是否能運作
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    # 如果都失敗，強制使用最標準的名稱
    return genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)

model = load_model()

# 啟動對話 Session
if "chat" not in st.session_state:
    # 修改：直接從回應中獲取第一句話，啟動感官
    st.session_state.chat = model.start_chat(history=[])
    # 這裡強制讓 AI 說出第一句開場白
    with st.spinner("大師正在準備..."):
        response = st.session_state.chat.send_message("請開始第一階段：確認身分")
        st.session_state.first_msg = response.text

# 渲染歷史對話
if "first_msg" in st.session_state and not st.session_state.chat.history:
    with st.chat_message("assistant"):
        st.markdown(st.session_state.first_msg)

for message in st.session_state.chat.history:
    role = "user" if message.role == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 輸入框與邏輯
if prompt := st.chat_input("你想對大師說什麼？"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        response = st.session_state.chat.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"連線異常，請稍後再試。錯誤代碼：{e}")
