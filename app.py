import streamlit as st
import requests
import json

# --- 1. 全局页面配置 ---
st.set_page_config(
    page_title="元气Agent - 你的生活小搭子",
    page_icon="✨",
    layout="wide",  # 使用宽屏模式以便更好地控制布局
    initial_sidebar_state="expanded"
)

# --- 2. 核心 CSS 注入 (复刻设计的关键) ---
st.markdown("""
<style>
    /* --- 全局基础设定 --- */
    .stApp {
        background-color: #ffffff; /* 纯白背景 */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* 隐藏 Streamlit 默认元素 */
    header[data-testid="stHeader"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* --- 侧边栏美化 --- */
    [data-testid="stSidebar"] {
        background-color: #f7f8fa; /* 极淡的灰色背景 */
        border-right: none;
    }
    [data-testid="stSidebarNav"] {
        padding-top: 20px;
    }
    /* 模拟侧边栏标题样式 */
    .sidebar-group-title {
        color: #999;
        font-size: 12px;
        margin-top: 20px;
        margin-bottom: 10px;
        padding-left: 10px;
    }

    /* --- 主区域头部样式 --- */
    .main-header-container {
        text-align: center;
        margin-top: 40px;
        margin-bottom: 40px;
    }
    .header-icon {
        font-size: 60px;
        color: #6366f1; /* 蓝紫色 */
    }
    .header-title {
        font-size: 28px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 10px;
    }
    .header-subtitle {
        font-size: 14px;
        color: #6b7280;
    }

    /* --- 功能卡片 (Feature Cards) CSS --- */
    .feature-card-container {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
    }
    .feature-card {
        background-color: #f8f9fa; /* 卡片淡灰背景 */
        border-radius: 16px;
        padding: 20px;
        flex: 1;
        display: flex;
        align-items: flex-start;
        gap: 15px;
        border: 1px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .feature-card:hover {
        border-color: #e5e7eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .card-icon-box {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        color: white;
        flex-shrink: 0;
    }
    .card-title {
        font-weight: 600;
        font-size: 16px;
        color: #333;
        margin-bottom: 4px;
    }
    .card-desc {
        font-size: 12px;
        color: #888;
        line-height: 1.4;
    }

    /* --- 聊天输入框区域美化 --- */
    /* 调整底部输入框容器的内边距和背景 */
    [data-testid="stBottom"] > div {
        padding-bottom: 20px;
        background: linear-gradient(to top, #ffffff 80%, rgba(255,255,255,0));
    }
    
    /* 输入框本身 */
    .stChatInput textarea {
        border-radius: 24px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
        padding-left: 45px !important; /* 留出位置假装有图标 */
        background-color: #fff !important;
    }
    /* 调整发送按钮颜色 */
    [data-testid="stChatInputSubmitButton"] {
        color: #6366f1 !important;
    }
    
    /* 底部声明文字 */
    .footer-disclaimer {
        text-align: center;
        font-size: 11px;
        color: #ccc;
        margin-top: -15px;
        margin-bottom: 10px;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. 安全读取 Key ---
try:
    DIFY_API_KEY = st.secrets["DIFY_API_KEY"]
except FileNotFoundError:
    st.error("请配置 Secrets")
    st.stop()
BASE_URL = "https://api.dify.ai/v1"

# --- 4. 初始化 Session ---
if "messages" not in st.session_state:
    # 初始状态不显示任何消息，只显示欢迎界面
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

# --- 5. 侧边栏布局 (尽力模拟设计稿) ---
with st.sidebar:
    st.markdown("### ✨ 元气Agent")
    
    if st.button("＋ 新建对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = ""
        st.rerun()
        
    st.markdown('<div class="sidebar-group-title">今天</div>', unsafe_allow_html=True)
    st.caption("📄 高血压饮食建议")
    st.caption("🩺 体检报告解读")

    st.markdown('<div class="sidebar-group-title">昨天</div>', unsafe_allow_html=True)
    st.caption("💊 感冒药咨询")
    st.caption("😴 失眠改善方法")
    
    st.markdown('<div class="sidebar-group-title">7天内</div>', unsafe_allow_html=True)
    st.caption("🥦 维生素D补充建议")
    
    # 底部用户区域用 expander 模拟
    st.markdown("---")
    with st.expander("👤 我的账户"):
        st.write("设置")
        st.write("退出登录")


# --- 6. 主界面布局核心逻辑 ---

# 如果没有聊天记录，显示欢迎主页和卡片
if not st.session_state.messages:
    # 使用三列布局，中间列占主导，让内容居中
    empty_col1, center_col, empty_col2 = st.columns([1, 3, 1])
    
    with center_col:
        # 6.1 头部欢迎区 (HTML)
        st.markdown("""
            <div class="main-header-container">
                <div style="font-size: 48px;">✨</div>
                <div class="header-title">你好，我是你的生活小搭子</div>
                <div class="header-subtitle">我会尽力提供参考建议（但是不能替代医生诊断哦）</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 6.2 功能卡片区 (HTML + CSS Grid 模拟)
        # 第一行卡片
        st.markdown("""
            <div class="feature-card-container">
                <div class="feature-card">
                    <div class="card-icon-box" style="background-color: #ff4d4f;">💊</div>
                    <div>
                        <div class="card-title">用药咨询</div>
                        <div class="card-desc">查询药物相互作用、用法用量</div>
                    </div>
                </div>
                <div class="feature-card">
                    <div class="card-icon-box" style="background-color: #ffc53d;">📄</div>
                    <div>
                        <div class="card-title">报告解读</div>
                        <div class="card-desc">上传体检报告，获取分析建议</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 第二行卡片
        st.markdown("""
            <div class="feature-card-container">
                 <div class="feature-card">
                    <div class="card-icon-box" style="background-color: #52c41a;">🥦</div>
                    <div>
                        <div class="card-title">膳食计划</div>
                        <div class="card-desc">定制健康饮食方案</div>
                    </div>
                </div>
                <div class="feature-card">
                    <div class="card-icon-box" style="background-color: #40a9ff;">🩺</div>
                    <div>
                        <div class="card-title">症状问诊</div>
                        <div class="card-desc">描述不舒服的症状，智能分析</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 添加一些空行，把输入框顶到底部
        st.write("")
        st.write("")


# --- 7. 聊天交互区 ---

# 显示历史消息 (为了配合设计稿，这里不使用头像，只显示纯文本气泡)
# 使用居中布局来约束聊天气泡的宽度
msg_col1, msg_center, msg_col2 = st.columns([1, 3, 1])
with msg_center:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 处理用户输入
# 注：Streamlit 原生输入框无法完美实现设计稿输入框内部的“回形针”图标
if prompt := st.chat_input("输入你的健康问题，或上传医疗报告..."):
    # 一旦有输入，页面刷新后就不会再显示上面的欢迎卡片了
    st.session_state.messages.append({"role": "user", "content": prompt})
    with msg_center:
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
                "user": "streamlit-v3-user"
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
                    st.error("服务稍后重试")
                    full_response = "连接异常"

            except Exception as e:
                st.error("网络错误")
                full_response = "网络请求失败"

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 8. 底部声明 (HTML) ---
# 使用 CSS 将其定位到输入框下方
st.markdown('<div class="footer-disclaimer">内容仅供参考，不构成医疗诊断建议</div>', unsafe_allow_html=True)
