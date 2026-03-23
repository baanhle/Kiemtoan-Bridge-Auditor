import math
from schemas import TCVNAuditInput, TCVNAuditOutput, CapacityResult, DetailsTCVN

class TCVNEngine:
    def __init__(self, input_data: TCVNAuditInput):
        self.data = input_data

    def calculate_beta1(self) -> float:
        """Hệ số khối ứng suất chữ nhật beta1 (TCVN 11823-5:2017 - Điều 5.7.2.2)"""
        f_c = self.data.materials.f_c
        if f_c <= 28.0:
            return 0.85
        else:
            beta1 = 0.85 - 0.05 * ((f_c - 28.0) / 7.0)
            return max(beta1, 0.65)

    def calculate_k_factor(self) -> float:
        """Hệ số loại cáp k (TCVN 11823-5:2017 - Điều 5.7.3.1.1)"""
        f_py_f_pu_ratio = self.data.materials.f_py / self.data.materials.f_pu
        if f_py_f_pu_ratio >= 0.90:  # Low relaxation
            return 0.28
        elif f_py_f_pu_ratio >= 0.85: # Stress-relieved
            return 0.38
        else:
            return 0.48 # Default fallback

    def calculate_flexural_resistance(self) -> CapacityResult:
        """Tính Sức kháng uốn (Flexural Resistance)"""
        geom = self.data.geometry
        mats = self.data.materials
        rebar = self.data.flexural_rebar
        forces = self.data.forces

        beta1 = self.calculate_beta1()
        k = self.calculate_k_factor()
        
        A_ps = rebar.A_ps
        f_pu = mats.f_pu
        # Tính toán d_p từ y_p (khoảng cách thớ dưới)
        d_p = geom.h - rebar.y_p
        # Cập nhật dp vào rebar để dùng cho các hàm khác nếu cần
        rebar.d_p = d_p
        
        b = geom.b
        f_c = mats.f_c
        
        A_s = rebar.A_s
        f_y = mats.f_y
        d_s = rebar.d_s
        
        A_prime_s = rebar.A_prime_s
        d_prime_s = rebar.d_prime_s

        # 1. Tính chiều sâu trục trung hòa c
        # Giả thiết ban đầu: Tiết diện chữ nhật (hoặc trục trung hòa nằm trong bản cánh)
        numerator_rect = (A_ps * f_pu) + (A_s * f_y) - (A_prime_s * f_y)
        denominator_rect = (0.85 * f_c * beta1 * b) + (k * A_ps * f_pu / d_p)
        c = numerator_rect / denominator_rect if denominator_rect != 0 else 0
        a = beta1 * c
        
        is_t_section = False
        # Nếu a > h_f, tính lại theo tiết diện chữ T
        if a > geom.h_f:
            is_t_section = True
            b_w = geom.b_w
            h_f = geom.h_f
            numerator_t = (A_ps * f_pu) + (A_s * f_y) - (A_prime_s * f_y) - (0.85 * f_c * (b - b_w) * h_f)
            denominator_t = (0.85 * f_c * beta1 * b_w) + (k * A_ps * f_pu / d_p)
            c = numerator_t / denominator_t if denominator_t != 0 else 0
            a = beta1 * c

        # 2. Ứng suất cáp khi phá hoại
        f_ps = f_pu * (1 - k * (c / d_p)) if d_p > 0 else 0
        
        # 3. Sức kháng danh định Mn
        if not is_t_section:
            # Tiết diện chữ nhật
            M_n = (A_ps * f_ps * (d_p - a/2) + 
                   A_s * f_y * (d_s - a/2) - 
                   A_prime_s * f_y * (d_prime_s - a/2))
        else:
            # Tiết diện chữ T (Bổ sung thành phần bản cánh theo công thức Sếp nhắc)
            # Mn = [Phần sườn] + [Phần cánh nhô ra]
            b_w = geom.b_w
            h_f = geom.h_f
            # Lưu ý công thức Sếp đưa ra: alpha1 * f'c * hf * (a/2 - hf/2) 
            # Đây là thành phần moment của cánh nhô ra đối với trọng tâm khối nén sườn
            M_n = (A_ps * f_ps * (d_p - a/2) + 
                   A_s * f_y * (d_s - a/2) - 
                   A_prime_s * f_y * (d_prime_s - a/2) +
                   0.85 * f_c * (b - b_w) * h_f * (a/2 - h_f/2))
        
        # 4. Kiểm tra điều kiện dẻo và quá cốt thép
        # Theo TCVN 11823-5:2017 Điều 5.7.3.3.1: c/de <= 0.42
        # Ở đây ta kiểm tra c/dp sơ bộ
        is_over_reinforced = False
        warning_msg = ""
        if d_p > 0:
            c_de_ratio = c / d_p
            if c_de_ratio > 0.42:
                is_over_reinforced = True
                warning_msg = f"CẢNH BÁO: Tiết diện quá cốt thép (c/dp={c_de_ratio:.2f} > 0.42). " \
                              "Sức kháng có thể bị giảm do bê tông bị ép vỡ trước khi thép đạt cường độ."

        # Đổi đơn vị từ N.mm sang kN.m
        M_n_kNm = M_n * 1e-6
        
        phi_f = 1.0 
        capacity = phi_f * M_n_kNm
        demand = forces.M_u
        
        ratio = demand / capacity if capacity != 0 else 0
        is_passed = capacity >= demand and not is_over_reinforced

        # Lưu trung gian
        self.c = c
        self.a = a
        self.f_ps = f_ps

        res_details = f"Mn={M_n_kNm:.2f} kNm, a={a:.2f} mm, fps={f_ps:.2f} MPa"
        if warning_msg:
            res_details += " | " + warning_msg

        return CapacityResult(
            capacity=capacity,
            demand=demand,
            ratio=ratio,
            is_passed=is_passed,
            details=res_details
        )

    def calculate_shear_resistance(self) -> CapacityResult:
        """Tính Sức kháng cắt (Shear Resistance - MCFT Simplified)"""
        geom = self.data.geometry
        mats = self.data.materials
        rebar = self.data.flexural_rebar
        shear = self.data.shear_rebar
        forces = self.data.forces

        # Tính toán chiều sâu hữu hiệu chịu cắt d_v (Điều 5.8.2.9)
        d_e = (rebar.A_ps * mats.f_pu * rebar.d_p + rebar.A_s * mats.f_y * rebar.d_s) / \
              (rebar.A_ps * mats.f_pu + rebar.A_s * mats.f_y) if (rebar.A_ps + rebar.A_s) != 0 else 0
              
        a = getattr(self, 'a', 0)
        d_v_1 = d_e - a / 2
        d_v_2 = 0.9 * d_e
        d_v_3 = 0.72 * geom.h
        d_v = max(d_v_1, d_v_2, d_v_3)

        # Sử dụng phương pháp MCFT đơn giản (Giả định góc nứt theta và beta nếu thỏa mãn cốt đai tối thiểu)
        # NOTE: Phiên bản phức tạp cần tính biến dạng dọc epsilon_x và tra bảng TCVN
        beta = 2.0 # Giả định đơn giản cho non-prestressed/hoặc prestressed
        theta_deg = 45.0
        theta_rad = math.radians(theta_deg)
        
        # Phiên bản DUL có thể dùng thư viện tính lặp. Tạm thời sử dụng hardcode cho form logic
        # V_c = 0.083 * beta * sqrt(f'c) * bw * dv
        V_c = 0.083 * beta * math.sqrt(mats.f_c) * geom.b_w * d_v
        
        # Sức kháng của cốt đai V_s
        alpha_rad = math.radians(shear.alpha)
        # Vs = (Av * fy * dv * (cot(theta) + cot(alpha)) * sin(alpha)) / s
        cot_theta = 1.0 / math.tan(theta_rad)
        cot_alpha = 1.0 / math.tan(alpha_rad) if alpha_rad != math.pi/2 else 0
        sin_alpha = math.sin(alpha_rad)
        
        V_s = (shear.A_v * mats.f_y * d_v * (cot_theta + cot_alpha) * sin_alpha) / shear.s
        
        # Đổi đơn vị sang kN
        V_c_kN = V_c * 1e-3
        V_s_kN = V_s * 1e-3
        
        V_p_kN = 0.0 # Bỏ qua thành phần lực nén đứng của cáp (conservative)
        
        V_n_kN = V_c_kN + V_s_kN + V_p_kN
        
        # Max Shear capacity limit: 0.25 * f'c * b_v * d_v
        V_n_limit_kN = (0.25 * mats.f_c * geom.b_w * d_v) * 1e-3
        V_n_kN = min(V_n_kN, V_n_limit_kN)
        
        phi_v = 0.9 # Hệ số sức kháng cắt
        capacity = phi_v * V_n_kN
        demand = forces.V_u
        
        ratio = demand / capacity if capacity != 0 else 0
        is_passed = capacity >= demand

        # Lưu trung gian
        self.d_e = d_e
        self.d_v = d_v
        self.theta = theta_deg
        self.beta = beta
        self.V_c_kN = V_c_kN
        self.V_s_kN = V_s_kN

        return CapacityResult(
            capacity=capacity,
            demand=demand,
            ratio=ratio,
            is_passed=is_passed,
            details=f"Vc={V_c_kN:.2f} kN, Vs={V_s_kN:.2f} kN, dv={d_v:.2f} mm"
        )

    def run_audit(self) -> TCVNAuditOutput:
        """Hàm chính kích hoạt chạy toàn bộ tính toán"""
        flex_result = self.calculate_flexural_resistance()
        shear_result = self.calculate_shear_resistance()
        
        overall = "ĐẠT" if (flex_result.is_passed and shear_result.is_passed) else "KHÔNG ĐẠT"
        
        details = DetailsTCVN(
            c=self.c,
            a=self.a,
            f_ps=self.f_ps,
            d_e=self.d_e,
            d_v=self.d_v,
            theta=self.theta,
            beta=self.beta,
            V_c=self.V_c_kN,
            V_s=self.V_s_kN
        )
        
        return TCVNAuditOutput(
            flexural=flex_result,
            shear=shear_result,
            details=details,
            overall_status=overall
        )

# Dành cho Testing khi chạy script trực tiếp
if __name__ == "__main__":
    pass
