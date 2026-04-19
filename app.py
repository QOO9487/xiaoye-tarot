import streamlit as st
import google.generativeai as genai
import re

# 1. 網頁頁面標題
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：AI塔羅諮詢")

# 2. API Key 設定
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# 3. 灌入占卜大師靈魂 (System Instruction)
instruction = """
[核心人格]
你是一位具備資深背景與極高洞察力的塔羅占卜大師。語氣沉穩、睿智且專業。
[第一階段：確認身分]
對話啟動時，第一句話必須且只能是：您好！請問我該如何稱呼你？
[第二階段：能量校準]
得到稱呼後，要求對方提供三張牌進行能量校準。解析時必須明確斷言對方的生理性別。
[第三階段：專業解析]
根據牌陣進行深度解讀。若牌數較多（如九宮格），請務必分析牌與牌之間的關聯性。
[語氣規範]
請使用台灣慣用的口吻與詞彙（例如：機率、連結）。描述年齡時，直接說「約30多歲」，嚴禁使用「20代」等非本土說法。
"""

# 4. 模型載入函數（支援動態切換）
def get_model(is_complex=False):
    # 判斷要使用哪種等級的大腦
    model_id = "models/gemini-3.1-pro-preview" if is_complex else "models/gemini-3.1-flash-preview"
    return genai.GenerativeModel(
        model_name=model_id,
        system_instruction=instruction
    )

# 5. 初始化對話紀錄
if "messages" not in st.session_state:
    # 預設啟動用 Flash
    initial_model = get_model(is_complex=False)
    st.session_state.chat = initial_model.start_chat(history=[])
    try:
        response = st.session_state.chat.send_message("請依照指令，發起問候。")
        st.session_state.messages = [{"role": "assistant", "content": response.text}]
    except Exception:
        st.session_state.messages = [{"role": "assistant", "content": "您好！請問我該如何稱呼你？"}]

# 6. 渲染畫面
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. 使用者輸入邏輯
if prompt := st.chat_input("請輸入您的稱呼或占卜訊息...", key="main_chat_v4"):
    # 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 偵測是否為複雜牌陣（例如：出現超過 6 個關鍵字或明確提到九宮格）
    # 這裡用簡單的逗號或空格分隔來預估牌數
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or "九宮格" in prompt or "六芒星" in prompt

    # 顯示大師回應
    with st.chat_message("assistant"):
        with st.spinner("大師感應中..." if not is_complex else "大師深度感應中（啟動高階邏輯）..."):
            try:
                # 若需要切換大腦，則重新啟動對話但帶入舊歷史
                if is_complex:
                    # 重新建立 Pro 模型的 chat 並帶入歷史紀錄
                    history = st.session_state.chat.history
                    st.session_state.chat = get_model(is_complex=True).start_chat(history=history)

                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                if "429" in str(e):
                    st.warning("大師感應次數已達上限，請稍候再試。")
                else:
                    st.error(f"連線異常：{e}")
