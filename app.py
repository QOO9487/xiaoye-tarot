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

genai.configure(api_key=API_KEY)

# 3. 灌入占卜大師靈魂 (System Instruction)
instruction = """
[核心人格]
你是一位具備資深背景與極高洞察力的塔羅占卜大師。語氣沉穩、睿智且專業。
[第一階段：確認身分]
對話啟動時，第一句話必須且只能是：您好！請問我該如何稱呼你？
[第二階段：三牌校準]
得到稱呼後，要求對方提供三張牌。解析時必須明確斷言「生理男」或「生理女」。
[語氣規範]
請使用台灣慣用的口吻。描述年齡時，直接說「約30多歲」，嚴禁使用「20代」這種說法。
"""

# 4. 初始化模型 (強制使用你清單中測試成功的 2.5 版本)
@st.cache_resource
def load_tarot_master():
    return genai.GenerativeModel(
        model_name="models/gemini-2.5-flash",
        system_instruction=instruction
    )

model = load_tarot_master()

# 5. 初始化對話紀錄 (使用 messages 列表，過濾掉後台指令)
if "messages" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    try:
        # 在後台啟動第一次問候
        response = st.session_state.chat.send_message("請依照指令，發起問候。")
        st.session_state.messages = [{"role": "assistant", "content": response.text}]
    except Exception:
        st.session_state.messages = [{"role": "assistant", "content": "您好！請問我該如何稱呼你？"}]

# 6. 渲染畫面
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. 使用者輸入邏輯 (全檔僅此一個輸入框)
if prompt := st.chat_input("請輸入您的稱呼或占卜訊息...", key="main_chat_v3"):
    # 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 顯示大師回應
    with st.chat_message("assistant"):
        with st.spinner("大師感應中..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                # 針對配額限制(429)給予提示
                if "429" in str(e):
                    st.warning("大師感應次數已達上限，請稍候半小時再試。")
                else:
                    st.error(f"連線異常：{e}")


import google.generativeai as genai
import streamlit as st

# 1. 配置 API Key
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    st.write("### --- 您的 API 可用模型清單 ---")
    
    try:
        # 獲取原始模型列表
        models = genai.list_models()
        
        # 建立一個簡單的清單來顯示，避免讀取不存在的屬性
        model_list = []
        for m in models:
            # 只要印出名稱就好，這絕對不會報錯
            model_list.append({
                "模型 ID": m.name,
                "模型標題": m.display_name
            })
            
        # 直接把結果顯示在 Streamlit 畫面上，表格化最清楚
        st.table(model_list)
        
    except Exception as e:
        st.error(f"獲取清單時發生預期外錯誤：{e}")
else:
    st.error("請確認 Streamlit Secrets 中已設定 GOOGLE_API_KEY")
