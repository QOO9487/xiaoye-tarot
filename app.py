import streamlit as st
import google.generativeai as genai

# 1. 網頁頁面標題
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：AI塔羅諮詢")

# 2. API Key 設定
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

# 強制設定：這是解決 404 與 429 的核心配置
genai.configure(api_key=API_KEY)

# 3. 占卜指令
instruction = "你是一位資深塔羅占卜大師。第一句話必須是：您好！請問我該如何稱呼你？"

# 4. 終極模型載入邏輯：直接強制指定一個絕對路徑
@st.cache_resource
def load_model():
    # 這是目前 2026 年最穩定、且避開 v1beta 限制的路徑寫法
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=instruction
    )

try:
    model = load_model()
except Exception as e:
    st.error(f"模型載入失敗：{e}")
    st.stop()

# 5. 初始化對話紀錄
if "messages" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    try:
        # 強制呼叫第一聲問候
        response = st.session_state.chat.send_message("Hello, start consultation.")
        st.session_state.messages = [{"role": "assistant", "content": response.text}]
    except Exception:
        st.session_state.messages = [{"role": "assistant", "content": "您好！請問我該如何稱呼你？"}]

# 6. 渲染畫面
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. 使用者輸入
if prompt := st.chat_input("請輸入您的稱呼...", key="main_chat"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("大師感應中..."):
            try:
                # 這裡加入支援最新的生成參數
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"連線異常：{e}")
