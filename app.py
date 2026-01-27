import streamlit as st
import requests
import json

# --- 1. 页面基础设置 (修改了标题和布局) ---
st.set_page_config(
    page_title="VitalHealth AI",
    page_icon="🩺",
    layout="centered", # 居中布局更像手机App，适合聊天
    initial_sidebar_state="expanded"
)

# --- 2. 自定义 CSS (隐藏无关元素，美化界面) ---
st.markdown("""
<style>
    /* 隐藏 Streamlit 默认的汉堡菜单和页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 调整聊天输入框的样式 */
    .stChatInput {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 安全读取 Key ---
try:
    DIFY_API_KEY = st.secrets["DIFY_API_KEY"]
except FileNotFoundError:
    st.error("请在 Streamlit Cloud 配置 Secrets")
    st.stop()

BASE_URL = "https://api.dify.ai/v1"

# --- 4. 初始化 Session ---
if "messages" not in st.session_state:
    # 默认给一个开场白
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是 VitalHealth 智能医生。👨‍⚕️\n我可以为您解读体检报告、提供健康建议。\n请告诉我您哪里不舒服？"}
    ]
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

# --- 5. 侧边栏设计 (增加专业感) ---
with st.sidebar:
    # 这里可以使用 emoji，也可以用 st.image 放你的 Logo 图片
    st.header("🩺 VitalHealth AI")
    st.markdown("---")
    st.markdown("**功能介绍：**")
    st.info("📊 报告解读\n💊 用药咨询\n🏃 运动建议")
    
    st.markdown("---")
    # 增加一个重置按钮
    if st.button("🗑️ 清空对话记录", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = ""
        st.rerun() # 重新加载页面

# --- 6. 聊天主界面 ---
st.title("💬 智能健康咨询")
st.caption("🚀 由 Dify 大模型驱动的医疗助手")

# 显示历史消息
for message in st.session_state.messages:
    # 根据角色设置不同的头像
    if message["role"] == "user":
        avatar = "👤" # 用户头像
    else:
        avatar = "👨‍⚕️" # 医生头像 (也可以换成图片URL)
        
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 处理输入
if prompt := st.chat_input("请描述您的症状或粘贴报告内容..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👨‍⚕️"):
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
            "user": "streamlit-pro-user"
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
                st.error("服务暂时繁忙，请稍后再试")
                full_response = "连接异常"

        except Exception as e:
            st.error("网络请求失败")
            full_response = "网络错误"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
