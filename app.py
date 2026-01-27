import streamlit as st
import requests
import json

# --- 页面配置 ---
st.set_page_config(page_title="VitalHealth AI", page_icon="🩺")
st.title("🩺 VitalHealth AI 智能健康助手")

# --- 安全读取 API Key ---
# 我们不再直接把 Key 写在这里，而是从 Streamlit 的云端配置中读取
try:
    DIFY_API_KEY = st.secrets["DIFY_API_KEY"]
except FileNotFoundError:
    st.error("请在 Streamlit Cloud 的 Secrets 设置中配置 DIFY_API_KEY")
    st.stop()

# 请将这里替换为你 Dify 的实际 API 服务器地址
BASE_URL = "https://api.dify.ai/v1" 

# --- 初始化会话 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

# --- 显示历史消息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 处理用户输入 ---
if prompt := st.chat_input("请输入您的健康咨询问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": {},
            "query": prompt,
            "response_mode": "streaming",
            "conversation_id": st.session_state.conversation_id,
            "user": "streamlit-web-user"
        }

        try:
            response = requests.post(
                f"{BASE_URL}/chat-messages",
                headers=headers,
                json=data,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            json_str = decoded_line[5:]
                            try:
                                json_data = json.loads(json_str)
                                if not st.session_state.conversation_id:
                                    st.session_state.conversation_id = json_data.get('conversation_id', "")
                                answer = json_data.get('answer', '')
                                full_response += answer
                                message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                continue
                message_placeholder.markdown(full_response)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                full_response = "系统连接异常"

        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            full_response = "网络请求失败"

    st.session_state.messages.append({"role": "assistant", "content": full_response})