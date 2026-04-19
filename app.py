import streamlit as st
import google.generativeai as genai
import re

# ==========================================
# 1. 核心參數與安全性設定
# ==========================================
if "ACCESS_PASSWORD" in st.secrets:
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
else:
    st.error("請在 Streamlit Secrets 中設定 ACCESS_PASSWORD")
    st.stop()

st.set_page_config(page_title="小葉占卜師", page_icon="🔮", layout="centered")
st.title("🔮 小葉占卜師：AI 塔羅諮詢")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# ==========================================
# 2. 占卜大師「高階邏輯」提示詞
# ==========================================
instruction = """
[核心人格]
你是一位資深、沉穩且具備極高洞察力的塔羅大師。說話簡練，重視意念與能量的對位。

[第一階段：確認身分]
第一句話固定為：「您好！請問我該如何稱呼你？」

[第二階段：能量校準 (絕對簡潔)]
當對方提供三張校準牌時：
1. 僅限判定：生理男/女、大概年齡區間（如：約30多歲）。
2. 嚴禁：嚴禁提及現狀描述、壓力分析或任何額外預測。
3. 結語：直接詢問：「[稱呼]，校準完畢。請告訴我你今天想諮詢的問題是什麼？」

[第三階段：診斷與抽牌引導]
當客戶提出問題，你必須評估牌陣。
1. 視覺觀想引導：必須告知客戶抽牌時內心應想著什麼畫面（例如：想像你們最後一次見面的情景）。
2. 建議牌陣：
   - 聖三角（3張）：過去、現在、未來。
   - 二選一（5張）：路徑A、路徑B、兩者對比。
   - 六芒星（6張）：關係現狀、阻礙、潛意識。
   - 九宮格（9張）：全方位運勢掃描。
3. 排版規範：簡明扼要，每一張牌位僅用 5-10 個字描述意義，嚴禁長篇大論。

[第四階段：深度解析與延伸判斷]
當客戶對解析提出疑問或後續想法時，你必須自動執行「決策邏輯」：
- 情況 A (深層挖掘)：若問題涉及原本牌陣的細節，請直接從舊牌中尋找更深層訊息，無需抽牌。
- 情況 B (行動導航)：若問題涉及新的決策、未知的變數或需要具體建議，請告知：「針對這部分，我們需要額外抽取 1-3 張『建議牌』。」並重複抽牌引導流程。
"""

# ==========================================
# 3. 初始化 Session State (記憶體與模型切換)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0
    st.session_state.unlocked = False
    st.session_state.current_model_id = "models/gemini-2.5-flash" 
    
    # 初始對話
    st.session_state.chat = genai.GenerativeModel(
        st.session_state.current_model_id, system_instruction=instruction
    ).start_chat(history=[])
    
    try:
        response = st.session_state.chat.send_message("請依照指令，發起問候。")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception:
        st.session_state.messages.append({"role": "assistant", "content": "您好！請問我該如何稱呼你？"})

with st.sidebar:
    st.header("🔮 占卜導航")
    st.info("校準 > 建議牌陣與觀想 > 深度解析 > (選填) 抽取建議牌。")
    st.caption("小葉設計 | 機械邏輯輔助神祕學")

# 4. 渲染聊天視窗
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. 密碼攔截 (第三題)
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
                st.success("解鎖成功！")
                st.rerun()
            else:
                st.error("密碼錯誤")
    st.stop() 

# 6. 使用者輸入
if prompt := st.chat_input("請輸入您的稱呼、牌名或疑問...", key="main_chat_v8"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.question_count += 1
    
    # 判斷是否啟動 Pro 大腦 (針對九宮格或長文解析)
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "深度", "分析"])
    target_model = "models/gemini-2.5-pro" if is_complex else "models/gemini-2.5-flash"

    with st.chat_message("assistant"):
        loading_msg = "大師解析中..." if is_complex else "大師感應中..."
        with st.spinner(loading_msg):
            try:
                # 記憶遷移邏輯
                if st.session_state.current_model_id != target_model:
                    history = st.session_state.chat.history
                    st.session_state.chat = genai.GenerativeModel(
                        target_model, system_instruction=instruction
                    ).start_chat(history=history)
                    st.session_state.current_model_id = target_model 

                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"連線異常，請稍後重試。")

st.divider()
st.caption("© 2026 小葉設計")
