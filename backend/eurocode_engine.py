import math
from schemas import TCVNAuditInput, TCVNAuditOutput, CapacityResult, DetailsTCVN

class EurocodeEngine:
    """
    Tiêu chuẩn Eurocode 2 (EN 1992-1-1)
    """
    def __init__(self, input_data: TCVNAuditInput):
        self.data = input_data
        self.data.standard = "EUROCODE 2"

    def calculate_lambda_eta(self):
        """Tính hệ số lambda và eta cho khối ứng suất (EN 1992-1-1 3.1.7)"""
        f_ck = self.data.materials.f_c # fck ở Eurocode tương đương f'c 
        # Hệ số lambda xác định chiều cao khối ứng suất
        lam = 0.8 if f_ck <= 50 else 0.8 - (f_ck - 50) / 400
        # Hệ số eta xác định cường độ hữu hiệu
        eta = 1.0 if f_ck <= 50 else 1.0 - (f_ck - 50) / 200
        return lam, eta

    def calculate_flexural_resistance(self) -> CapacityResult:
        """Tính Sức kháng uốn Mrd (Bending Moment Resistance)"""
        geom = self.data.geometry
        mats = self.data.materials
        rebar = self.data.flexural_rebar
        forces = self.data.forces

        lam, eta = self.calculate_lambda_eta()
        
        # Eurocode partial safety factors (gamma_c = 1.5, gamma_s = 1.15)
        # EN 1992-1-1 3.3.6: f_pd = f_p0.1k / gamma_s
        f_cd = (eta * mats.f_c) / 1.5 
        f_yd = mats.f_y / 1.15
        f_pd = mats.f_py / 1.15 # f_py ở đây tương đương f_p0.1k (giới hạn chảy 0.1%)
        
        A_ps = rebar.A_ps
        d_p = rebar.d_p
        b = geom.b
        A_s = rebar.A_s
        d_s = rebar.d_s
        
        # Tính chiều sâu khối ứng suất (x)
        numerator = (A_ps * f_pd) + (A_s * f_yd)
        denominator = (lam * f_cd * b)
        x = numerator / denominator if denominator != 0 else 0
        
        a = lam * x
        
        # M_Rd
        M_Rd = (A_ps * f_pd * (d_p - a/2) + A_s * f_yd * (d_s - a/2))
        M_Rd_kNm = M_Rd * 1e-6
        
        capacity = M_Rd_kNm
        demand = forces.M_u
        
        ratio = demand / capacity if capacity != 0 else 0
        is_passed = capacity >= demand

        self.c = x
        self.a = a
        self.f_ps = f_pd * 1.15 # Lấy lại giá trị danh định để hiển thị

        return CapacityResult(
            capacity=capacity,
            demand=demand,
            ratio=ratio,
            is_passed=is_passed,
            details=f"MRd={M_Rd_kNm:.2f} kNm, x={x:.2f} mm"
        )

    def calculate_shear_resistance(self) -> CapacityResult:
        """Tính sức kháng cắt VRd theo EN 1992-1-1 (Simplified)"""
        geom = self.data.geometry
        mats = self.data.materials
        rebar = self.data.flexural_rebar
        shear = self.data.shear_rebar
        forces = self.data.forces

        d = max(rebar.d_p, rebar.d_s)
        z = 0.9 * d # Cánh tay đòn nội lực
        
        # V_Rd,s (Cốt đai chịu cắt) - Variable strut inclination method
        theta_deg = 45.0 # Eurocode cho phép 21.8 <= theta <= 45. Lấy 45 là bảo thủ nhất
        theta_rad = math.radians(theta_deg)
        alpha_rad = math.radians(shear.alpha)
        
        f_ywd = mats.f_y / 1.15
        
        cot_theta = 1.0 / math.tan(theta_rad)
        cot_alpha = 1.0 / math.tan(alpha_rad) if alpha_rad != math.pi/2 else 0
        sin_alpha = math.sin(alpha_rad)
        
        # VRd,s = (Asw / s) * z * fywd * (cot(theta) + cot(alpha)) * sin(alpha)
        V_Rds = (shear.A_v / shear.s) * z * f_ywd * (cot_theta + cot_alpha) * sin_alpha
        
        # V_Rd,max (Bê tông sườn phá hoại nén)
        nu_1 = 0.6 * (1 - mats.f_c / 250)
        f_cd = mats.f_c / 1.5
        V_Rdmax = (shear.alpha == 90.0) * (geom.b_w * z * nu_1 * f_cd / (math.tan(theta_rad) + 1.0/math.tan(theta_rad)))
        if shear.alpha != 90.0:
             V_Rdmax = geom.b_w * z * nu_1 * f_cd * (cot_theta + cot_alpha) / (1 + cot_theta**2)
        
        V_Rds_kN = V_Rds * 1e-3
        V_Rdmax_kN = V_Rdmax * 1e-3
        
        capacity = min(V_Rds_kN, V_Rdmax_kN)
        demand = forces.V_u
        
        ratio = demand / capacity if capacity != 0 else 0
        is_passed = capacity >= demand

        self.beta = 1.0 # Placeholder
        self.theta = theta_deg
        self.V_c_kN = 0.0 # Eurocode tách thành VRdc (không cốt đai) hoặc VRds (có cốt đai). Không cộng dồn
        self.V_s_kN = V_Rds_kN
        self.d_e = d
        self.d_v = z

        return CapacityResult(
            capacity=capacity,
            demand=demand,
            ratio=ratio,
            is_passed=is_passed,
            details=f"VRds={V_Rds_kN:.2f} kN, VRdmax={V_Rdmax_kN:.2f} kN"
        )

    def run_audit(self) -> TCVNAuditOutput:
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
