import streamlit as st
import math

st.set_page_config(page_title="Tính Toán Dầm BTCT Tự Động - TCVN 5574", layout="wide")

st.title("Ứng dụng tính toán kết cấu dầm BTCT tự động")
st.write("Tiêu chuẩn áp dụng: **TCVN 5574:2018** | Tùy chọn linh hoạt Mác bê tông, Cốt thép, tự động tính nội lực và cốt thép Gối - Nhịp.")

# --- Phần 1: Cấu hình vật liệu dạng tùy chọn (Sidebar hoặc ngay đầu trang) ---
st.sidebar.header("1. Cấu hình vật liệu chung")

# Tùy chọn Mác bê tông (Quy đổi ra cường độ tính toán Rb theo TCVN 5574)
concrete_grade = st.sidebar.selectbox(
    "Chọn Mác / Cấp độ bền bê tông:",
    ["B15 (C12/15) - Rb = 8.5 MPa", 
     "B20 (C16/20) - Rb = 11.5 MPa", 
     "B25 (C20/25) - Rb = 14.5 MPa", 
     "B30 (C25/30) - Rb = 17.0 MPa", 
     "B35 (C30/37) - Rb = 19.5 MPa"],
    index=2 # Mặc định B25
)

# Gán giá trị Rb tương ứng
if "B15" in concrete_grade: Rb = 8.5
elif "B20" in concrete_grade: Rb = 11.5
elif "B25" in concrete_grade: Rb = 14.5
elif "B30" in concrete_grade: Rb = 17.0
else: Rb = 19.5

# Tùy chọn Mác / Loại cốt thép dọc (Quy đổi ra Rs)
steel_grade = st.sidebar.selectbox(
    "Chọn Loại Cốt Thép Dọc:",
    ["CB300-V (Rs = 260 MPa)", "CB400-V (Rs = 350 MPa)"],
    index=0 # Mặc định CB300-V
)

Rs = 260.0 if "CB300" in steel_grade else 350.0
a_cover = st.sidebar.number_input("Lớp bảo vệ cốt thép a (mm)", value=30.0, step=5.0)

# --- Phần 2: Chọn số lượng đoạn nhịp ---
st.header("2. Sơ đồ kết cấu hệ dầm")
num_spans = st.number_input("Chọn số lượng đoạn dầm/nhịp liên tiếp:", min_value=1, max_value=15, value=3, step=1)

st.markdown("---")
st.subheader("3. Nhập thông số hình học và tải trọng thành phần cho từng nhịp")

beam_data = []

# Tiêu đề bảng nhập liệu
col_h = st.columns([0.8, 1.1, 1.1, 1.1, 1.1, 1.4, 1.4])
col_h[0].markdown("**Nhịp**")
col_h[1].markdown("**Ký hiệu**")
col_h[2].markdown("**Nhịp L (m)**")
col_h[3].markdown("**b × h (mm)**")
col_h[4].markdown("**Cao tường (m)**")
col_h[5].markdown("**Tải sàn (kN/m)**")
col_h[6].markdown("**Hệ số nhịp (M)**")

for i in range(int(num_spans)):
    c0, c1, c2, c3, c4, c5, c6 = st.columns([0.8, 1.1, 1.1, 1.1, 1.1, 1.4, 1.4])
    with c0:
        st.markdown(f"**#{i+1}**")
    with c1:
        b_name = st.text_input(f"Tên {i+1}", value=f"D{i+1}", key=f"name_{i}", label_visibility="collapsed")
    with c2:
        l_val = st.number_input(f"L_{i+1}", value=5.0, step=0.1, key=f"L_{i}", label_visibility="collapsed")
    with c3:
        sec_val = st.text_input(f"Sec_{i+1}", value="200x400", key=f"sec_{i}", label_visibility="collapsed")
    with c4:
        wall_h = st.number_input(f"Wall_{i+1}", value=3.2, step=0.1, key=f"wall_{i}", label_visibility="collapsed")
    with c5:
        floor_q = st.number_input(f"Floor_{i+1}", value=10.0, step=0.5, key=f"floor_{i}", label_visibility="collapsed")
    with c6:
        m_type = st.selectbox(f"Mtype_{i+1}", ["Dầm liên tục (ql²/10)", "Dầm đơn giản (ql²/8)"], key=f"mtype_{i}", label_visibility="collapsed")
    
    # Tách tiết diện b và h từ chuỗi (ví dụ: "200x400" -> b=200, h=400)
    try:
        parts = sec_val.lower().split('x')
        b_val = float(parts[0].strip())
        h_val = float(parts[1].strip())
    except:
        b_val, h_val = 200.0, 400.0
        
    beam_data.append({
        "name": b_name, 
        "L": l_val, 
        "b": b_val, 
        "h": h_val, 
        "wall_h": wall_h,
        "floor_q": floor_q,
        "m_type": m_type
    })

# --- Hàm chọn thép thực tế tự động ---
def select_steel(As_req):
    if As_req <= 400:
        return "3Φ14 (As = 462 mm²)"
    elif As_req <= 600:
        return "3Φ16 (As = 603 mm²)"
    elif As_req <= 760:
        return "3Φ18 (As = 763 mm²)"
    elif As_req <= 940:
        return "3Φ20 (As = 942 mm²)"
    else:
        return "4Φ20 (As = 1257 mm²)"

# --- Phần 4: Nút tính toán tự động ---
st.markdown("---")
if st.button("🚀 Tự động tính toán Nội lực (M, Q) và Cốt thép Gối - Nhịp", type="primary"):
    st.header("4. Bảng kết quả tính toán chi tiết")
    
    results = []
    has_error = False
    
    for item in beam_data:
        b = item["b"]
        h = item["h"]
        L = item["L"]
        h0 = h - a_cover
        
        # 1. Tự động tính tải trọng phân bố q (kN/m)
        q_beam = 1.1 * (b / 1000.0) * (h / 1000.0) * 25.0
        q_wall = 1.2 * item["wall_h"] * 0.2 * 18.0
        q_floor = 1.2 * item["floor_q"]
        q_total = q_beam + q_wall + q_floor
        
        # 2. Tự động tính Mô-men (M) và Lực cắt (Q)
        if "liên tục" in item["m_type"]:
            M_span = (q_total * (L ** 2)) / 10.0
            M_support = (q_total * (L ** 2)) / 9.0
        else:
            M_span = (q_total * (L ** 2)) / 8.0
            M_support = M_span * 0.2 
            
        Q_max = (q_total * L) / 2.0 
        
        # 3. Tính cốt thép tại NHỊP và GỐI
        M_span_Nmm = M_span * 1e6
        alpha_m_span = M_span_Nmm / (Rb * b * (h0 ** 2))
        
        M_sup_Nmm = M_support * 1e6
        alpha_m_sup = M_sup_Nmm / (Rb * b * (h0 ** 2))
        
        alpha_R = 0.429
        
        if alpha_m_span > alpha_R or alpha_m_sup > alpha_R:
            results.append({
                "Đoạn dầm": item["name"],
                "Nhịp L (m)": L,
                "Tải q (kN/m)": f"{q_total:.2f}",
                "Trạng thái": f"⚠️ Lỗi: Tiết diện {b}x{h} quá nhỏ so với tải trọng!"
            })
            has_error = True
        else:
            x_span = h0 * (1 - math.sqrt(1 - 2 * alpha_m_span))
            As_span = (Rb * b * x_span) / Rs
            
            x_sup = h0 * (1 - math.sqrt(1 - 2 * alpha_m_sup))
            As_sup = (Rb * b * x_sup) / Rs
            
            results.append({
                "Đoạn dầm": item["name"],
                "Nhịp L (m)": L,
                "Tải q (kN/m)": f"{q_total:.2f}",
                "M nhịp / Gối (kN.m)": f"Nhịp: {M_span:.1f} | Gối: {M_support:.1f}",
                "Lực cắt Q (kN)": f"{Q_max:.1f}",
                "Thép Nhịp (As = {:.0f}mm²)".format(As_span): select_steel(As_span),
                "Thép Gối (As = {:.0f}mm²)".format(As_sup): select_steel(As_sup)
            })
            
    # Hiển thị bảng kết quả
    st.table(results)
    
    if has_error:
        st.warning("⚠️ Có dầm bị quá tải do tiết diện nhỏ. Hãy tăng kích thước tiết diện b x h lên!")
    else:
        st.success("✅ Đã tự động tính toán hoàn tất nội lực và bố trí thép Gối - Nhịp thành công!")
