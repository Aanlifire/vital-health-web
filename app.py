import streamlit as st
import requests
import json

# --- 1. 全局配置 (必须是第一个 Streamlit 命令) ---
st.set_page_config(
    page_title="VitalHealth AI",
    page_icon="🩺",
    layout="wide",  # 使用宽屏模式，显得大气
    initial_sidebar_state="expanded"
)

# --- 2. 高级 CSS 注入 (这是变美的核心) ---
# 我们使用 CSS 覆盖 Streamlit 的默认样式，打造“医疗科技感”
st.markdown("""
<style>
    /* 全局字体与背景 - 使用柔和的渐变背景 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 隐藏 Streamlit 默认的顶部红线、汉堡菜单和页脚 */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
        border-right: 1px solid #f0f0f0;
    }

    /* 聊天气泡样式优化 */
    /* 用户气泡：深蓝色背景，白色文字，圆润 */
    [data-testid="chatAvatarIcon-user"] {
        background-color: #007bff !important;
    }
    .stChatMessage.user {
        background-color: #e3f2fd;
        border-radius: 20px 20px 0 20px;
    }

    /* 机器人气泡：白色背景，轻微阴影 */
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #28a745 !important;
    }
    
    /* 输入框美化 - 悬浮效果 */
    .stChatInputContainer {
        padding-bottom: 20px;
    }
    .stChatInput {
        border-radius: 30px;
        border: 1px solid #ddd;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* 标题样式 */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* 按钮样式 */
    .stButton>button {
        border-radius: 20px;
        border: none;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff2b2b;
        transform: scale(1.05);
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
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是 **VitalHealth** 智能医生。👨‍⚕️\n\n我可以为您：\n- 📄 **解读体检报告**\n- 💊 **分析用药禁忌**\n- 🥗 **提供饮食建议**\n\n请直接告诉我您的症状，或粘贴报告内容。"}
    ]
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

# --- 5. 侧边栏设计 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/doctor-male--v1.png", width=80)
    st.title("VitalHealth AI")
    st.caption("v2.0 Professional")
    
    st.markdown("---")
    st.markdown("#### 💡 使用指南")
    st.info("请详细描述您的症状，例如：\n'我最近总是头痛，尤其是下午，血压是140/90，应该怎么办？'")
    
    st.markdown("#### ⚙️ 设置")
    # 一个美化的重置按钮
    if st.button("🔄 开启新对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = ""
        st.rerun()

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px;'>Powered by Dify & Streamlit</div>", unsafe_allow_html=True)

# --- 6. 主界面布局 ---

# 使用列布局来居中内容，防止在宽屏下太散
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("<h1>🩺 智能健康咨询助手</h1>", unsafe_allow_html=True)
    
    # 显示历史消息
    for message in st.session_state.messages:
        avatar = "👤" if message["role"] == "user" else "👨‍⚕️"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # 处理输入
    if prompt := st.chat_input("在此输入您的健康问题..."):
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
