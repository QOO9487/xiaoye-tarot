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
# 側邊欄公告 (保留原始樣式)
# ==========================================
with st.sidebar:
    st.header("🔮 關於小葉占卜師")
    st.info("""
    本平台由 **小葉** 研發設計，旨在提供深度、專業的塔羅諮詢體驗。
    
    ### 💡 使用說明
    * **初步體驗**：開放前兩次提問體驗塔羅牌占卜的樂趣。
    * **深度諮詢**：為避免陌生人消耗AI算力，**從第三個問題起**，系統將要求輸入「通行密碼」。
    
    ### 🔑 如何獲取密碼？
    如欲繼續進行深度占卜，請私訊 **小葉** 索取專屬密碼，即可解鎖後續無限次諮詢。
    """)
    st.caption("技術支援：Gemini 2.5 Pro & Flash")

# ==========================================
# 2. 占卜大師靈魂設定
# ==========================================
instruction = """
[核心人格]
你是一位資深、沉穩且具備極高洞察力的塔羅大師。語氣簡練、專業。

[第一階段：確認身分]
對話啟動時，第一句話固定為：「您好！請問我該如何稱呼你？」

[第二階段：能量校準]
當對方提供三張牌時，僅限判定：生理男/女、大概年齡區間（如：約30多歲）。
禁忌：其餘內容皆不用說，保持極簡。
校準完畢後，詢問客戶：「[稱呼]，校準完畢。請告訴我你今天想諮詢的問題是什麼？」

[第三階段：診斷與抽牌建議]
當客戶提出問題：
1. 意念觀想引導：告知客戶抽牌時內心應想著什麼畫面。
2. 建議牌陣：簡明扼要列出抽牌順序與每張牌代表的問題。每一張牌位意義僅限 10 字以內。

[第四階段：深度解析與續抽判斷]
解牌時結合校準背景。若客戶後續提問，自動評估：是否需延續解析或「追加 1-3 張建議牌」。
"""

# ==========================================
# 3. 初始化 Session State
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0
    st.session_state.unlocked = False
    st.session_state.pending_prompt = None  # 🔮 暫存區：解決「重複輸入」問題的關鍵
    st.session_state.current_model_id = "models/gemini-2.5-flash" 
    
    st.session_state.chat = genai.GenerativeModel(
        st.session_state.current_model_id, system_instruction=instruction
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
# 5. 使用者輸入捕獲 (關鍵修正：搬移到攔截邏輯之前)
# ==========================================
# 無論是否解鎖，先提供輸入框
prompt = st.chat_input("請輸入您的稱呼、牌名或疑問...", key="main_chat_v13")

# 如果使用者輸入了內容
if prompt:
    # 情況 A：這不是第三題，或是已經解鎖，直接處理
    if st.session_state.question_count != 2 or st.session_state.unlocked:
        # 直接進入處理流程
        pass 
    # 情況 B：這是第三題且未解鎖，將內容存入「暫存區」並重新整理來觸發鎖頭
    else:
        st.session_state.pending_prompt = prompt
        st.rerun()

# ==========================================
# 6. 密碼攔截機制 (優化：如果暫存區有東西，自動銜接)
# ==========================================
if st.session_state.question_count == 2 and not st.session_state.unlocked:
    # 如果暫存區已經有剛才輸入的問題，顯示出來讓使用者安心
    if st.session_state.pending_prompt:
        with st.chat_message("user"):
            st.markdown(st.session_state.pending_prompt)
        st.warning("🔮 **問題已接收。請輸入通行密碼解鎖，大師將立即為您解析：**")
    else:
        st.warning("🔮 **校準完成。請在此輸入通行密碼以開啟深度諮詢：**")

    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("輸入密碼", type="password", label_visibility="collapsed", key="lock_pwd")
    with col2:
        if st.button("確認解鎖", use_container_width=True):
            if pwd_input == ACCESS_PASSWORD:
                st.session_state.unlocked = True
                # 🔮 核心自動化：解鎖成功後，如果有暫存問題，直接存入對話紀錄
                if st.session_state.pending_prompt:
                    prompt = st.session_state.pending_prompt
                    st.session_state.pending_prompt = None # 清空暫存
                    # 這裡不 rerun，直接讓下方的解析邏輯跑完
                else:
                    st.success("解鎖成功！請開始提問。")
                    st.rerun()
            else:
                st.error("密碼錯誤")
    
    # 如果還沒解鎖，且目前也沒有要自動處理的問題，就停止
    if not st.session_state.unlocked:
        st.stop()

# ==========================================
# 7. 使用者提問與大師回應邏輯
# ==========================================
if prompt:
    # 將問題加入對話紀錄
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.question_count += 1
    
    # 判斷模型等級
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "深度", "分析"])
    target_model = "models/gemini-2.5-pro" if is_complex else "models/gemini-2.5-flash"

    with st.chat_message("assistant"):
        with st.spinner("大師感應中..."):
            try:
                # 記憶遷移與模型切換
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
