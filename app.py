import streamlit as st
import google.generativeai as genai
import os

st.title("🛠️ 小葉占卜師：終極連線測試")

# 1. 強制設定 API 環境
API_KEY = "AIzaSyAKkfy479-Itbg9LMFziX7pQr8YXq_3x28"
os.environ["GOOGLE_API_KEY"] = API_KEY
genai.configure(api_key=API_KEY)

# 2. 測試連線邏輯
if st.button("啟動終極測試"):
    try:
        # 這裡不直接寫名稱，改用清單抓取目前伺服器「看得到」的模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        st.write("目前伺服器可用的型號：", available_models)
        
        # 強制挑選一個來測試
        target_model = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
        
        model = genai.GenerativeModel(model_name=target_model)
        response = model.generate_content("Hello, system test.")
        
        st.success(f"✅ 成功！使用型號：{target_model}")
        st.balloons()
        st.write(f"AI 回應：{response.text}")
        
    except Exception as e:
        st.error(f"❌ 依舊失敗。底層錯誤訊息：{e}")
        st.info("請檢查 GitHub 的 requirements.txt 是否正確寫入：google-generativeai>=0.8.3")
