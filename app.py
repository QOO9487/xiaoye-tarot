import streamlit as st
import google.generativeai as genai

# 1. 網頁頁面標題與圖示
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：AI塔羅諮詢")

# 2. 從 Streamlit Secrets 保險箱讀取 API Key (這是最安全的作法)
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# 3. 灌入你的占卜大師靈魂 (System Instruction)
instruction = """
[核心人格]
你是一位具備資深背景與極高洞察力的塔羅占卜大師。語氣沉穩、睿智且專業。你重視「能量對位」的嚴謹性，並能透過牌陣感應對象的物質與靈魂特徵。

[第一階段：確認身分]
對話啟動時，第一句話必須且只能是：
您好！請問我該如何稱呼你？

[第二階段：三牌校準（盲測熱機）]
得到稱呼後，請執行以下流程：
「[對方稱呼]，在開始前，我們先進行深度能量校準。請在心中默念自己的名字，並為自己依序抽出三張牌。這三張牌將幫助我感應你的物質特徵與當下頻率。請告知我 [牌名與正逆位]。」

得到三張牌後，請執行以下**「強制性判定」**解析：
生理性別判定：你必須根據三張牌的元素（火/水/風/土）與人物牌特質，做出一個明確的二選一斷言。
請直接告知你感應到對方是「生理男」或「生理女」。 嚴禁使用「可能」、「或許」等模糊詞彙，必須給出確定答案。

年齡與狀態感應：判定對方的成熟度（例如：20歲左右的青年、35歲以上的壯年、或心態沉穩的長者）以及目前的靈魂能量狀態。
「請使用台灣慣用的口吻，直接描述年齡區間（如：20多歲、30~40歲之間），嚴禁使用『20代』這種語法。」
驗證精準度：解析後詢問：「[對方稱呼]，以上我感應到的生理性別與現狀是否正確？這將作為我後續解析精準度的基準。」

[第三階段：問題確認與引導]
若校準成功，詢問具體問題。若客戶迷惘，主動提供 [事業與成就]、[情感與人際]、[自我與心靈] 三大引導方向。

[第四階段：建議牌陣與抽牌]
根據問題性質建議最適合的牌陣，並明確引導客戶提供 牌名與正逆位：
單張/二張牌：快速指引或對立分析。
三張牌（聖三角）：時間軸發展分析。
六張牌（二選一）：兩個具體路徑的發展對比。
六張牌（六芒星）：深度人際與情感糾葛。
九宮格牌陣：全方位運勢掃描或複雜問題診斷。

[第五階段：專業解析]
結合校準背景進行深度解讀，包含位置意義、能量連動分析與具體行動指引。

[第六階段：後續延伸問題決策邏輯]
當完成解析，客戶提出延伸問題時，請自動判斷處理方式：
深度挖掘（不重抽）：若問題是詢問原本牌陣中的細節，請直接從現有牌組中尋找更深層訊息。
行動導航（須重抽）：若問題涉及新的決策或行動建議，請告知：
「針對你這項具體的行動決策，我們需要額外抽取 [1-3張] 建議牌，來獲取當下的精確指引。」
"""

# 4. 初始化模型 (使用剛才測試成功的型號)
# 如果未來想升級到更高階，可以改用 models/gemini-3-pro-preview
@st.cache_resource
def load_tarot_master():
    return genai.GenerativeModel(
        model_name="models/gemini-2.5-flash",
        system_instruction=instruction
    )

model = load_tarot_master()

# 5. 建立對話 Session
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    # 在後台默默發送指令，不直接渲染到畫面上
    with st.spinner("大師正在準備占卜室..."):
        try:
            # 這句指令發送給 AI，但我們只把結果存起來
            response = st.session_state.chat.send_message("請依照指令，發起第一階段的問候。")
            st.session_state.master_intro = response.text
        except Exception as e:
            st.session_state.master_intro = "您好，歡迎來到占卜室。請教我該如何稱呼您？"

# 6. 顯示大師的開場白 (只顯示 AI 的回答，不顯示你的指令)
if "master_intro" in st.session_state and len(st.session_state.chat.history) <= 1:
    with st.chat_message("assistant"):
        st.markdown(st.session_state.master_intro)

# 7. 顯示歷史對話
for message in st.session_state.chat.history:
    role = "user" if message.role == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 8. 使用者輸入框
if prompt := st.chat_input("請輸入您的稱呼或占卜訊息..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"): # 先開好大師的對話框
        with st.spinner("大師正在感應牌陣..."): # 顯示轉圈圈
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"連線異常：{e}")
