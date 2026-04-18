import streamlit as st
import google.generativeai as genai

# 1. 網頁基本設定
st.set_page_config(page_title="小葉占卜師", page_icon="🔮")
st.title("🔮 小葉占卜師：專業塔羅諮詢")

# 2. 設定 API Key (請注意安全性，建議之後更換新 Key)
# 提醒：你目前的 Key 已公開，建議稍後前往 AI Studio 重新產生並替換
API_KEY = "AIzaSyAKkfy479-Itbg9LMFziX7pQr8YXq_3x28" 
genai.configure(api_key=API_KEY)

# 3. 占卜大師指令
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
生理性別判定：你必須根據三張牌的元素（火/水/風/土）與人物牌特質，做出一個明確的二選一斷言。請直接告知你感應到對方是「生理男」或「生理女」。 嚴禁使用「可能」、「或許」等模糊詞彙，必須給出確定答案。
年齡與狀態感應：判定對方的成熟度（例如：20歲左右的青年、35歲以上的壯年、或心態沉穩的長者）以及目前的靈魂能量狀態。
現狀掃描：描述對方近期生活中的一個具體變動或壓力核心。
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

# 4. 初始化模型 (使用最穩定的名稱)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=instruction
)

# 5. 啟動對話 Session
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# 6. 渲染歷史對話
for message in st.session_state.chat.history:
    # 這裡的邏輯：Google 的 role 是 user/model，Streamlit 建議轉為 user/assistant
    role = "user" if message.role == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 7. 輸入框與邏輯
if prompt := st.chat_input("你想對大師說什麼？"):
    # 顯示使用者的訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 呼叫 API 獲取回應
    try:
        response = st.session_state.chat.send_message(prompt)
        # 顯示大師的訊息
        with st.chat_message("assistant"):
            st.markdown(response.text)
    except Exception as e:
        # 如果報錯 404，通常是模型名稱或 API 版本問題
        st.error(f"連線異常，請稍後再試：{e}")
