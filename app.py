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
當對方提供三張牌時，僅判定：生理男/女、大概年齡區間（如：約30多歲）。
禁忌：其餘內容皆不用說，保持極簡。
校準完畢後，詢問客戶：「[稱呼]，校準完畢。請告訴我你今天想諮詢的問題是什麼？」

[第三階段：診斷與抽牌建議]
當客戶提出問題：
1. 意念觀想引導：告知客戶抽牌時內心應想著什麼畫面（這對占卜結果至關重要）。
2. 建議牌陣：簡明扼要列出抽牌順序與每張牌代表的問題。每一張牌位意義僅限 10 字以內。

[第四階段：深度解析與續抽判斷]
解牌時結合校準背景。若客戶後續提問，自動評估：
- 若涉及舊牌細節：延續解析。
- 若涉及新決策/變數：告知需「額外抽取 1-3 張建議牌」並給予新的觀想引導。
"""

# ==========================================
# 3. 初始化 Session State (加入暫存區)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_count = 0
    st.session_state.unlocked = False
    st.session_state.pending_prompt = None # 🔮 暫存區：存放解鎖前輸入的問題
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
# 5. 處理「暫存問題」的發送邏輯
# ==========================================
# 如果剛剛解鎖成功，且有暫存的問題，則在這裡自動觸發處理
if st.session_state.unlocked and st.session_state.pending_prompt:
    auto_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None # 清空暫存
    # 將暫存問題加入對話紀錄並執行 (邏輯同下方的 chat_input)
    with st.chat_message("user"):
        st.markdown(auto_prompt)
    st.session_state.messages.append({"role": "user", "content": auto_prompt})
    st.session_state.question_count += 1
    
    # 直接執行回應邏輯 (這裡簡化，下方的回應邏輯會處理它)
    # 為了讓流程順暢，我們設定一個變數讓下方直接跑 response
    st.session_state.force_response = auto_prompt

# ==========================================
# 6. 密碼攔截機制 (優化：偵測輸入並暫存)
# ==========================================
if st.session_state.question_count == 2 and not st.session_state.unlocked:
    st.markdown("---")
    st.warning("🔮 **校準完成。為了進行深度占卜與牌陣建議，請輸入通行密碼以繼續：**")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("輸入密碼", type="password", label_visibility="collapsed", key="lock_pwd")
    with col2:
        if st.button("確認解鎖", use_container_width=True):
            if pwd_input == ACCESS_PASSWORD:
                st.session_state.unlocked = True
                st.success("解鎖成功！正在為您導向大師解析...")
                st.rerun()
            else:
                st.error("密碼錯誤")
    
    # 🔮 核心優化：如果使用者在這個狀態下「硬要」輸入問題 (透過某些方式) 
    # 或者我們想在使用者看到鎖之前就存下內容
    if prompt_check := st.chat_input("請輸入您的問題 (輸入後請解鎖)..."):
        st.session_state.pending_prompt = prompt_check
        st.info("💡 問題已記錄，請輸入密碼解鎖後大師將立即回答。")
        st.rerun()

    st.stop() 

# ==========================================
# 7. 使用者提問與大師回應邏輯
# ==========================================
# 判斷是來自輸入框，還是來自剛剛解鎖後的「暫存發送」
prompt = st.chat_input("請輸入您的訊息...")
if "force_response" in st.session_state:
    prompt = st.session_state.pop("force_response")

if prompt:
    # 如果還沒被加入紀錄 (chat_input 進來的需要加入，暫存進來的上面已經加過)
    if not any(m["content"] == prompt for m in st.session_state.messages[-1:]):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.question_count += 1
    
    # 判斷模型
    card_count = len(re.split(r'[,，\s\n]+', prompt.strip()))
    is_complex = card_count >= 6 or any(kw in prompt for kw in ["九宮格", "六芒星", "深度", "分析"])
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
                st.error(f"大師暫時斷開連結，請稍後。")

st.divider()
st.caption("© 2026 小葉設計")
