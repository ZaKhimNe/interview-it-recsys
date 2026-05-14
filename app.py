"""
🚀 AI Tech Interview Prep - MINI DEMO
=====================================
Chạy: streamlit run app.py
"""

import streamlit as st
import random
from core.data_loader import load_question_bank
from ui.components.charts import create_radar_chart
from ui.session_manager import init_session_state, get_state, set_state
import numpy as np

# Khởi tạo state
init_session_state()

def main():
    st.set_page_config(page_title="AI Prep Demo", page_icon="🎯", layout="wide")
    
    st.title("🎯 AI Tech Interview Prep - Mini Demo")
    
    # 1. SIDEBAR - CHỌN ROLE
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        role = st.selectbox("Bạn muốn phỏng vấn vị trí nào?", ["DA", "DE", "DS", "BE"])
        if st.button("Bắt đầu lại (Reset)"):
            st.rerun()

    # 2. LOGIC ĐIỀU HƯỚNG DEMO
    if "demo_step" not in st.session_state:
        st.session_state.demo_step = "START"

    # --- BƯỚC 1: MÀN HÌNH CHÀO ---
    if st.session_state.demo_step == "START":
        st.info(f"Hệ thống đã sẵn sàng cho vị trí **{role}**. Nhấn nút bên dưới để bắt đầu câu hỏi đầu tiên.")
        if st.button("Bắt đầu Phỏng vấn"):
            # Lấy ngẫu nhiên 1 câu hỏi cho role này
            all_questions = load_question_bank()
            role_questions = [q for q in all_questions if q.get("roles", {}).get("primary") == role]
            
            if role_questions:
                st.session_state.current_q = random.choice(role_questions)
                st.session_state.demo_step = "INTERVIEW"
                st.rerun()
            else:
                st.error(f"Xin lỗi, hiện chưa có dữ liệu cho role {role}")

    # --- BƯỚC 2: MÀN HÌNH PHỎNG VẤN ---
    elif st.session_state.demo_step == "INTERVIEW":
        q = st.session_state.current_q
        st.subheader(f"❓ Câu hỏi: {q['question_id']}")
        st.write(q['question_text'])
        
        answer = st.text_area("Câu trả lời của bạn:", placeholder="Nhập câu trả lời tại đây...", height=150)
        
        if st.button("Gửi câu trả lời"):
            if answer:
                st.session_state.user_answer = answer
                st.session_state.demo_step = "RESULT"
                st.rerun()
            else:
                st.warning("Vui lòng nhập câu trả lời trước khi gửi!")

    # --- BƯỚC 3: MÀN HÌNH KẾT QUẢ ---
    elif st.session_state.demo_step == "RESULT":
        q = st.session_state.current_q
        st.success("✅ Đã ghi nhận câu trả lời!")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Đánh giá & Đáp án")
            st.write("**Câu trả lời của bạn:**", st.session_state.user_answer)
            with st.expander("Xem đáp án chuyên gia", expanded=True):
                st.write(q['answers']['detailed'])
                st.markdown("**Các ý chính cần có:**")
                for p in q['answers'].get('evaluation_points', []):
                    st.write(f"- {p}")
        
        with col2:
            st.subheader("📊 Biểu đồ Năng lực (Giả lập)")
            # Tạo vector năng lực giả lập để hiển thị Radar Chart
            # Trong thực tế, AI sẽ tính toán điểm này dựa trên câu trả lời
            mock_vector = np.array([7.5, 6.0, 8.5, 4.0, 5.5, 3.0])
            fig = create_radar_chart(mock_vector, title=f"Năng lực sau phỏng vấn {role}")
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 Lưu ý: Điểm số trên là giả lập cho Demo. Bản chính thức sẽ dùng AI để chấm điểm thật.")

        if st.button("Thử câu hỏi khác"):
            st.session_state.demo_step = "START"
            st.rerun()

if __name__ == "__main__":
    main()
