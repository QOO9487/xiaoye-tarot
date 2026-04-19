import streamlit as st
import google.generativeai as genai
import re

# ==========================================
# 1. 核心參數與安全性設定
# ==========================================
ACCESS_PASSWORD = "葉大師168"  # 🔮 在此修改你的通行密碼

# 網頁基礎配置
st.set_page_config(page_title="小葉占卜師", page_icon="🔮", layout="centered")
st.title("🔮 小葉占卜師：AI 塔羅諮詢")

# API Key 安全讀取
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# ==========================================
# 側邊欄公告 (說明付費與密碼機制)
# ==========================================
with st.sidebar:
    st.header("🔮 關於小葉占卜師")
    st.info("""
    本平台由 **小葉** 研發設計，旨在提供深度、專業的塔羅諮詢體驗。
    
    ### 💡 使用說明
    * **初步體驗**：開放前兩次提問免費體驗，讓您感受大師的能量。
    * **深度諮詢**：由於高階 AI 模型運算需支付雲端費用，**從第三個問題起**，系統將要求輸入「通行密碼」。
    
    ### 🔑 如何獲取密碼？
    如欲繼續進行深度占卜，請私訊 **小葉** 索取專屬密碼，即可解鎖後續無限次諮詢。
    """)
    st.caption("技術支援：Gemini 3.1 Pro & Flash")

# ==========================================
# 2. 占卜大師靈魂設定 (System Instruction)
# ==========================================
instruction = """
[核心人格]
你是一位具備資深背景與極高洞察力的塔羅占卜大師。語氣沉穩、睿智且專業。
[第一階段：確認身分]
對話啟動時，第一句話必須且只能是：您好！請問我該如何稱呼你？
[第二階段：能量校準]
得到稱呼後，要求對方提供三張牌進行能量校準。解析時必須明確斷言對方的生理性別。
[第三階段：專業解析]
根據牌陣進行深度解讀。若牌數較多（如九宮格），請務必分析牌與牌之間的關聯性、對角線與因果連結。
[語氣規範]
請使用台灣慣用的口吻（例如：機率、連結、對位）。描述年齡時，直接說「約30多歲」，嚴禁使用「20代」等非本土說法。
"""

# ==========================================
# 3. 初始化 Session State (記憶體管理)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0      # 提問計數
    st.session_state.unlocked = False        # 是否已過密碼鎖
    st.session_state.current_model_id = "models/gemini-3.1-flash-preview" # 初始預設模型
    
    # 建立初始 Flash 大腦
    initial_model = genai.GenerativeModel(
        model_name=st.session_state.current_model_id, 
        system_instruction=instruction
    )
    st.session_state.chat = initial_model.start_chat(history=[])
    
    # 自動發起大師問候 (不顯示指令)
    try:
        response = st.session_state.chat.send_message("請依照指令，發起問候。")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception:
        st.session_state.messages.append({"role": "assistant", "content": "您好！請問我該如何稱呼你？"})

# ==========================================
# 4. 渲染聊天視窗
# ==========================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 5. 密碼攔截機制 (第三題門檻)
# ==========================================
# 當使用者已經問過 2 個問題 (count=2)，且還沒解鎖時，攔截第 3 個問題
if st.session_state.question_count == 2 and not st.session_state.unlocked:
    st.markdown("---")
    st.warning("🔮 大師感應到深層能量，請輸入『通行密碼』以繼續深度諮詢：")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("輸入密碼", type="password", label_visibility="collapsed", key="lock_pwd")
    with col2:
        if st.button("確認解鎖", use_container_width=True):
            if pwd_input == ACCESS_PASSWORD:
                st.session_state.unlocked = True
                st.success("解鎖成功！請重新發送您的問題。")
                st.rerun()
            else:
                st.error("密碼錯誤")
    st.stop() 

# ==========================================
# 6. 使用者輸入邏輯 (動態切換大腦)
# ==========================================
if prompt := st.chat_input("請輸入您的稱呼或占卜訊息...", key="main_chat_v6"):
    # 1. 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. 增加提問計數
    st.session_state.question_count += 1
    
    # 3. 判斷負載：偵測牌數與關鍵字
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "二選一", "深度"])
    target_model = "models/gemini-3.1-pro-preview" if is_complex else "models/gemini-3.1-flash-preview"

    # 4. 執行大師回應
    with st.chat_message("assistant"):
        loading_msg = "大師啟動高階邏輯感應中..." if is_complex else "大師感應中..."
        with st.spinner(loading_msg):
            try:
                # 記憶遷移邏輯：熱切換大腦
                if st.session_state.current_model_id != target_model:
                    history = st.session_state.chat.history
                    st.session_state.chat = genai.GenerativeModel(
                        target_model, 
                        system_instruction=instruction
                    ).start_chat(history=history)
                    st.session_state.current_model_id = target_model 

                # 發送訊息
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                if "429" in str(e):
                    st.warning("大師目前感應過於頻繁，請稍候再試。")
                elif "404" in str(e):
                    st.error("系統路徑異常，請檢查模型名稱是否正確。")
                else:
                    st.error(f"連線異常：{e}")

# ==========================================
# 7. 頁尾資訊
# ==========================================
st.divider()
st.caption("© 2026 小葉占卜師 ")
