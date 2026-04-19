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
# 側邊欄公告 (保留您要求的原始樣式)
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
# 2. 占卜大師靈魂設定 (優化後的提示詞)
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
1. 意念觀想引導：告知客戶抽牌時內心應想著什麼畫面（這對占卜結果至關重要）。
2. 建議牌陣：簡明扼要列出抽牌順序與每張牌代表的問題。
   - 每一張牌位意義僅限 10 字以內，嚴禁冗長文字。

[第四階段：深度解析與續抽判斷]
解牌時結合校準背景。若客戶後續提問，自動評估是否需延續解析或「追加 1-3 張建議牌」並給予新的觀想引導。
"""

# ==========================================
# 3. 初始化 Session State
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0
    st.session_state.unlocked = False
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
# 5. 密碼攔截機制 (主動攔截流程優化)
# ==========================================
# 當使用者問完姓名(1)且送出校準牌(2)後，count 會變成 2。
# 下一步應該要問正式問題，此時我們直接彈出密碼框，並停止渲染下方的對話框。
if st.session_state.question_count == 2 and not st.session_state.unlocked:
    st.markdown("---")
    st.warning("🔮 **校準完成。為了進行深度占卜與牌陣建議，請先輸入通行密碼：**")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("輸入密碼", type="password", label_visibility="collapsed", key="lock_pwd")
    with col2:
        if st.button("確認解鎖", use_container_width=True):
            if pwd_input == ACCESS_PASSWORD:
                st.session_state.unlocked = True
                st.success("解鎖成功！")
                st.rerun() # 密碼正確，重新刷頁面，對話框就會出現了
            else:
                st.error("密碼錯誤")
    
    # 關鍵：這裡調用 stop()，確保下方的 st.chat_input 不會被顯示出來
    st.stop() 

# ==========================================
# 6. 使用者輸入邏輯
# ==========================================
# 只有在 unlocked=True 或者 question_count != 2 時，使用者才會看到這個輸入框
if prompt := st.chat_input("請輸入您的訊息...", key="main_chat_v11"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    st.session_state.question_count += 1
    
    # 動態判斷是否需要 Pro 大腦
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "深度", "解析"])
    target_model = "models/gemini-2.5-pro" if is_complex else "models/gemini-2.5-flash"

    with st.chat_message("assistant"):
        with st.spinner("大師感應中..."):
            try:
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
                st.error(f"連線異常，請稍後再試。")

# ==========================================
# 7. 頁尾資訊
# ==========================================
st.divider()
st.caption("© 2026 小葉設計")
