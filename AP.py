import streamlit as st
import math

st.set_page_config(page_title="Tính Toán Dầm Liên Tiếp & Tùy Chỉnh Tiết Diện", layout="wide")

st.title("Ứng dụng tính toán cốt thép dầm liên tục tự động")
st.write("Tiêu chuẩn áp dụng: **TCVN 5574:2018** | Hỗ trợ nhập liệu chi tiết từng đoạn nhịp và tùy chỉnh tiết diện độc lập.")

# --- Phần 1: Cấu hình thông số vật liệu chung (Sidebar) ---
st.sidebar.header("1. Thông số vật liệu chung")
Rb = st.sidebar.number_input("Cường độ chịu nén tính toán của bê tông Rb (MPa)", value=14.5, step=0.5)
Rs = st.sidebar.number_input("Cường độ chịu kéo tính toán của cốt thép Rs (MPa)", value=260.0, step=10.0)
a_cover = st.sidebar.number_input("Lớp bảo vệ cốt thép a (mm)", value=30.0, step=5.0)

# --- Phần 2: Chọn số lượng dầm/đoạn nhịp nối tiếp ---
st.header("2. Sơ đồ kết cấu và số lượng đoạn nhịp")
num_spans = st.number_input("Chọn số lượng đoạn dầm/nhịp nối tiếp nhau:", min_value=1, max_value=15, value=3, step=1)

# --- Hình minh họa sơ đồ dầm liên tục trực quan ---
st.markdown("---")
st.subheader("💡 Sơ đồ minh họa hệ dầm liên tục")
# Tạo giao diện hiển thị sơ đồ trực quan dựa trên số nhịp người dùng chọn
cols_diagram = st.columns(int(num_spans))
for i in range(int(num_spans)):
    with cols_diagram[i]:
        st.info(f"**Nhịp / Đoạn {i+1}**\n\n(L_{i+1}, b_{i+1} x h_{i+1})")
st.markdown("---")

# --- Phần 3: Bảng nhập kích thước và biến số riêng cho từng đoạn dầm ---
st.subheader("3. Nhập biến số, chiều dài và tùy chỉnh tiết diện cho từng đoạn dầm")

beam_data = []

# Tiêu đề bảng nhập liệu
col_h = st.columns([0.8, 1.2, 1.2, 1.2, 1.2, 1.5, 1.8])
col_h[0].markdown("**Đoạn**")
col_h[1].markdown("**Ký hiệu**")
col_h[2].markdown("**Nhịp L (m)**")
col_h[3].markdown("**Bề rộng b (mm)**")
col_h[4].markdown("**Chiều cao h (mm)**")
col_h[5].markdown("**Tải q (kN/m)**")
col_h[6].markdown("**Mô-men M (kN.m)**")

for i in range(int(num_spans)):
    c0, c1, c2, c3, c4, c5, c6 = st.columns([0.8, 1.2, 1.2, 1.2, 1.2, 1.5, 1.8])
    with c0:
        st.markdown(f"**#{i+1}**")
    with c1:
        b_name = st.text_input(f"Tên {i+1}", value=f"Nhịp {i+1}", key=f"name_{i}", label_visibility="collapsed")
    with c2:
        l_val = st.number_input(f"L_{i+1}", value=5.0, step=0.1, key=f"L_{i}", label_visibility="collapsed")
    with c3:
        b_val = st.number_input(f"b_{i+1}", value=200.0, step=10.0, key=f"b_{i}", label_visibility="collapsed")
    with c4:
        h_val = st.number_input(f"h_{i+1}", value=400.0, step=10.0, key=f"h_{i}", label_visibility="collapsed")
    with c5:
        q_val = st.number_input(f"q_{i+1}", value=12.5, step=0.5, key=f"q_{i}", label_visibility="collapsed")
    with c6:
        m_val = st.number_input(f"M_{i+1}", value=40.0, step=1.0, key=f"M_{i}", label_visibility="collapsed")
    
    beam_data.append({
        "name": b_name, 
        "L": l_val, 
        "b": b_val, 
        "h": h_val, 
        "q": q_val, 
        "M": m_val
    })

# --- Phần 4: Nút thực hiện tính toán và xuất kết quả ---
st.markdown("---")
if st.button("🚀 Thực hiện tính toán kết cấu toàn bộ hệ dầm", type="primary"):
    st.header("4. Bảng kết quả tính toán chi tiết theo TCVN 5574:2018")
    
    results = []
    has_error = False
    
    for item in beam_data:
        b = item["b"]
        h = item["h"]
        h0 = h - a_cover
        M = item["M"]
        M_Nmm = M * 1e6  # Đổi kN.m sang N.mm
        
        # Kiểm tra điều kiện chịu lực alpha_m
        alpha_m = M_Nmm / (Rb * b * (h0 ** 2))
        alpha_R = 0.429  # Giới hạn vùng nén
        
        if alpha_m > alpha_R:
            results.append({
                "Đoạn dầm": item["name"],
                "Nhịp L (m)": item["L"],
                "Tiết diện (mm)": f"{b:.0f} × {h:.0f}",
                "Mô-men M (kN.m)": M,
                "Trạng thái": f"⚠️ Lỗi: Tiết diện nhỏ (αm = {alpha_m:.3f} > {alpha_R})"
            })
            has_error = True
        else:
            # Tính chiều cao vùng nén x và diện tích cốt thép As
            x = h0 * (1 - math.sqrt(1 - 2 * alpha_m))
            As = (Rb * b * x) / Rs
            
            # Đề xuất chọn thép thực tế tối ưu
            if As <= 400:
                steel_choice = "3Φ14 (As = 462 mm²)"
            elif As <= 600:
                steel_choice = "3Φ16 (As = 603 mm²)"
            elif As <= 760:
                steel_choice = "3Φ18 (As = 763 mm²)"
            elif As <= 940:
                steel_choice = "3Φ20 (As = 942 mm²)"
            else:
                steel_choice = "4Φ20 (As = 1257 mm²)"
                
            results.append({
                "Đoạn dầm": item["name"],
                "Nhịp L (m)": item["L"],
                "Tiết diện (mm)": f"{b:.0f} × {h:.0f}",
                "Tải q (kN/m)": item["q"],
                "Mô-men M (kN.m)": M,
                "As yêu cầu (mm²)": f"{As:.1f}",
                "Thép chọn thực tế": steel_choice
            })
            
    # Hiển thị bảng kết quả ra giao diện
    st.table(results)
    
    if has_error:
        st.warning("⚠️ Phát hiện đoạn dầm có mô-men vượt quá khả năng chịu lực của tiết diện đã chọn. Hãy tăng chiều cao hoặc bề rộng tiết diện của đoạn đó!")
    else:
        st.success("✅ Đã tính toán và tối ưu cốt thép thành công cho toàn bộ các đoạn dầm nối tiếp!")