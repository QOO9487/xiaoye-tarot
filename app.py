import streamlit as st
import google.generativeai as genai
import re

# ==========================================
# 1. 核心參數與安全性設定
# ==========================================
# 強制從平台 Secrets 讀取通行密碼
if "ACCESS_PASSWORD" in st.secrets:
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
else:
    st.error("請在 Streamlit Secrets 中設定 ACCESS_PASSWORD (通行密碼)")
    st.stop()

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
# 側邊欄公告 (保留您指定的原始樣式)
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
    st.caption("技術支援：Gemini 2.5 Pro & Flash")

# ==========================================
# 2. 占卜大師靈魂設定 (升級版：觀想引導與續抽判斷)
# ==========================================
instruction = """
[核心人格]
你是一位資深、沉穩且具備極高洞察力的塔羅大師。語氣簡練、專業，重視意念與能量的對位。

[第一階段：確認身分]
對話啟動時，第一句話必須且只能是：您好！請問我該如何稱呼你？

[第二階段：能量校準]
當對方提供三張校準牌時：
1. 僅限判定：生理男/女、大概年齡區間（如：約30多歲）。
2. 禁忌：除此之外「其餘都不用說」，嚴禁分析現狀。
3. 結語：校準完畢後，詢問客戶今天想諮詢的問題是什麼。

[第三階段：診斷與抽牌建議]
當客戶提出問題時：
1. 意念觀想引導：必須明確告知客戶抽牌時內心應「觀想什麼畫面或問題」。
2. 建議牌陣：根據問題推薦牌陣（聖三角/二選一/六芒星/九宮格）。
3. 牌位描述：簡明扼要。每一張牌位僅需 5-10 個字描述其占卜意義，避免使用者閱讀疲勞。

[第四階段：解析與續抽判斷]
解析時結合校準背景。若客戶後續提出想法，你必須評估：
- 若問題涉及舊牌細節，則延續解析。
- 若問題涉及新決策或變數，則告知需額外抽取 1-3 張「建議牌」。
"""

# ==========================================
# 3. 初始化 Session State (記憶體管理)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0      # 提問計數
    st.session_state.unlocked = False        # 是否已過密碼鎖
    st.session_state.current_model_id = "models/gemini-2.5-flash" 
    
    # 建立初始對話
    st.session_state.chat = genai.GenerativeModel(
        model_name=st.session_state.current_model_id, 
        system_instruction=instruction
    ).start_chat(history=[])
    
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
# 當問完校準(count=2)準備提問時，直接攔截，隱藏下方輸入框
if st.session_state.question_count == 2 and not st.session_state.unlocked:
    st.markdown("---")
    st.warning("🔮 大師感應到深層能量需求，請輸入『通行密碼』以繼續深度諮詢：")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("輸入密碼", type="password", label_visibility="collapsed", key="lock_pwd")
    with col2:
        if st.button("確認解鎖", use_container_width=True):
            if pwd_input == ACCESS_PASSWORD:
                st.session_state.unlocked = True
                st.success("解鎖成功！請發送您的占卜問題。")
                st.rerun()
            else:
                st.error("密碼錯誤")
    st.stop() 

# ==========================================
# 6. 使用者輸入邏輯 (動態切換大腦)
# ==========================================
if prompt := st.chat_input("請輸入您的稱呼、牌名或疑問...", key="main_chat_v10"):
    # 1. 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. 增加提問計數
    st.session_state.question_count += 1
    
    # 3. 判斷負載
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "深度", "分析"])
    target_model = "models/gemini-2.5-pro" if is_complex else "models/gemini-2.5-flash"

    # 4. 執行大師回應
    with st.chat_message("assistant"):
        loading_msg = "大師感應中..."
        with st.spinner(loading_msg):
            try:
                # 熱切換大腦
                if st.session_state.current_model_id != target_model:
                    history = st.session_state.chat.history
                    st.session_state.chat = genai.GenerativeModel(
                        target_model, 
                        system_instruction=instruction
                    ).start_chat(history=history)
                    st.session_state.current_model_id = target_model 

                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"連線異常，請稍後再試。")

# ==========================================
# 7. 頁尾資訊
# ==========================================
st.divider()
st.caption("© 2026 小葉設計")
