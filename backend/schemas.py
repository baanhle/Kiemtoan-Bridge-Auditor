from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

# ==========================================
# 1. TCVN 11823-5:2017 INPUT MODELS (Đầu vào)
# ==========================================

class MaterialProperties(BaseModel):
    """Đặc trưng vật liệu theo TCVN 11823-5:2017"""
    # Bê tông
    f_c: float = Field(..., description="Cường độ chịu nén quy định của bê tông ở 28 ngày (fc') [MPa]")
    E_c: float = Field(..., description="Mô đun đàn hồi của bê tông (Ec) [MPa]")
    
    # Thép thường
    f_y: float = Field(..., description="Giới hạn chảy của cốt thép thường (fy) [MPa]")
    E_s: float = Field(200000.0, description="Mô đun đàn hồi cốt thép thường (Es) [MPa]")
    
    # Cáp dự ứng lực
    f_pu: float = Field(..., description="Cường độ kéo đứt quy định của cáp DUL (fpu) [MPa]")
    f_py: float = Field(..., description="Giới hạn chảy của cáp DUL (fpy) [MPa] (Thường = 0.9fpu)")
    E_p: float = Field(197000.0, description="Mô đun đàn hồi cáp DUL (Ep) [MPa]")
    f_pe: float = Field(..., description="Ứng suất hữu hiệu của cáp sau khi trừ tất cả bớt mát (fpe) [MPa]")

class SectionGeometry(BaseModel):
    """Thông số hình học mặt cắt ngang (Dùng chung Uốn & Cắt)"""
    h: float = Field(..., description="Chiều cao toàn bộ dầm (h) [mm]", gt=0)
    b: float = Field(..., description="Bề rộng cánh chịu nén hữu hiệu (b hoặc beff) [mm]", gt=0)
    b_w: float = Field(..., description="Bề rộng sườn dầm chịu cắt (bw) [mm]", gt=0)
    h_f: float = Field(..., description="Chiều dày bản cánh chịu nén (hf) [mm]", gt=0)
    A_g: float = Field(..., description="Diện tích nguyên mặt cắt (Ag) [mm2]", gt=0)
    I_g: float = Field(..., description="Moment quán tính nguyên (Ig) [mm4]", gt=0)

    @model_validator(mode='after')
    def check_physical_dimensions(self) -> 'SectionGeometry':
        if self.b_w > self.b:
            raise ValueError(f"Bề rộng sườn (bw={self.b_w}) không thể lớn hơn bề rộng cánh (b={self.b}).")
        if self.h_f >= self.h:
            raise ValueError(f"Chiều dày bản cánh (hf={self.h_f}) phải nhỏ hơn tổng chiều cao dầm (h={self.h}).")
        return self

class Reinforcement(BaseModel):
    """Bố trí Cốt thép & Cáp (Uốn)"""
    A_s: float = Field(0.0, description="Diện tích cốt thép thường chịu kéo (As) [mm2]", ge=0)
    d_s: float = Field(0.0, description="Khoảng cách từ thớ nén xa nhất đến trọng tâm As (ds) [mm]", ge=0)
    A_prime_s: float = Field(0.0, description="Diện tích cốt thép thường chịu nén (A's) [mm2]", ge=0)
    d_prime_s: float = Field(0.0, description="Khoảng cách từ thớ nén xa nhất đến trọng tâm A's (d's) [mm]", ge=0)
    A_ps: float = Field(..., description="Diện tích cáp dự ứng lực (Aps) [mm2]", gt=0)
    d_p: float = Field(..., description="Khoảng cách từ thớ nén xa nhất đến trọng tâm cáp (dp) [mm]", gt=0)

class ShearReinforcement(BaseModel):
    """Bố trí cốt đai (Cắt)"""
    A_v: float = Field(..., description="Diện tích cốt thép đai trong khoảng cách s (Av) [mm2]", gt=0)
    s: float = Field(..., description="Khoảng cách cốt đai (s) [mm]", gt=0)
    alpha: float = Field(90.0, description="Góc nghiêng cốt thép đai so với trục dọc (alpha) [độ]", gt=0, le=90)

class InternalForces(BaseModel):
    """Nội lực thiết kế (Tổ hợp Cường độ/Sử dụng)"""
    M_u: float = Field(..., description="Moment uốn cực hạn (Mu) [kN.m]")
    V_u: float = Field(..., description="Lực cắt cực hạn (Vu) [kN]")
    N_u: float = Field(0.0, description="Lực dọc trục cùng thời điểm (Nu) (+ Kéo, - Nén) [kN]")

class TCVNAuditInput(BaseModel):
    """Tổng hợp INPUT cho Engine TCVN 11823:2017"""
    standard: str = Field("TCVN 11823:2017", description="Tiêu chuẩn áp dụng")
    materials: MaterialProperties
    geometry: SectionGeometry
    flexural_rebar: Reinforcement
    shear_rebar: ShearReinforcement
    forces: InternalForces
    
    @model_validator(mode='after')
    def check_reinforcement_depths(self) -> 'TCVNAuditInput':
        h = self.geometry.h
        if self.flexural_rebar.d_p >= h:
            raise ValueError(f"Khoảng cách dp ({self.flexural_rebar.d_p}) phải nhỏ hơn chiều cao dầm ({h}).")
        if self.flexural_rebar.A_s > 0 and self.flexural_rebar.d_s >= h:
             raise ValueError(f"Khoảng cách ds ({self.flexural_rebar.d_s}) phải nhỏ hơn chiều cao dầm ({h}).")
        return self

# ==========================================
# 2. OUTPUT MODELS (Kết quả)
# ==========================================

class CapacityResult(BaseModel):
    """Kết quả sức kháng chung"""
    capacity: float = Field(..., description="Sức kháng tính toán (vd: phi*Mn) [kN.m hoặc kN]")
    demand: float = Field(..., description="Nội lực yêu cầu (Mu/Vu) [kN.m hoặc kN]")
    ratio: float = Field(..., description="Tỷ số Demand/Capacity")
    is_passed: bool = Field(..., description="Đạt (True) / Không Đạt (False)")

class DetailsTCVN(BaseModel):
    """Trích xuất các biến trung gian để in Báo Cáo Word TCVN"""
    c: float = Field(..., description="Chiều sâu trục trung hòa (c) [mm]")
    a: float = Field(..., description="Chiều sâu khối ứng suất chữ nhật (a) [mm]")
    f_ps: float = Field(..., description="Ứng suất trung bình trong cáp DUL khi phá hoại (fps) [MPa]")
    d_e: float = Field(..., description="Chiều sâu hữu hiệu chịu cắt (de) [mm]")
    d_v: float = Field(..., description="Chiều sâu chịu cắt hiệu dụng (dv) [mm]")
    theta: float = Field(..., description="Góc nghiêng ứng suất nén chéo (theta) [độ]")
    beta: float = Field(..., description="Hệ số truyền lực kéo của bê tông nứt (beta)")
    V_c: float = Field(..., description="Sức kháng cắt danh định của Bê tông (Vc) [kN]")
    V_s: float = Field(..., description="Sức kháng cắt danh định của Cốt đai (Vs) [kN]")

class TCVNAuditOutput(BaseModel):
    """
    Mô hình chứa Output của bài toán chuẩn TCVN 11823:2017
    Gói luôn cả Input vào Output để in ra báo cáo Word một cách trọn vẹn.
    """
    input_data: Optional[TCVNAuditInput] = None # Cho phép null để Backward compatible
    flexural: CapacityResult
    shear: CapacityResult
    details: DetailsTCVN
    overall_status: str = Field(..., description="'ĐẠT' hoặc 'KHÔNG ĐẠT'")

if __name__ == "__main__":
    print(TCVNAuditInput.schema_json(indent=2))
