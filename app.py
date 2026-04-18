import streamlit as st
import google.generativeai as genai

st.title("🛠️ 小葉占卜師：系統連線測試")

# 請確保這組 Key 是你在截圖中看到的那組
API_KEY = "AIzaSyAKkfy479-Itbg9LMFziX7pQr8YXq_3x28"
genai.configure(api_key=API_KEY)

# 測試用的簡易提示詞
instruction = "你是一位占卜大師，現在正在進行系統測試。"

# 嘗試用最原始的方式建立模型
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=instruction
    )
    
    # 執行一次超微量測試
    if st.button("點擊測試連線"):
        response = model.generate_content("測試連線中，請回覆：連線成功")
        st.success(f"✅ 恭喜！連線成功。AI 回應：{response.text}")
        st.balloons()
        
except Exception as e:
    st.error(f"❌ 連線依舊失敗，錯誤訊息如下：")
    st.code(str(e))
    
    st.info("💡 解決建議：請確認 GitHub 中的 requirements.txt 是否已加入 google-generativeai>=0.8.3")
