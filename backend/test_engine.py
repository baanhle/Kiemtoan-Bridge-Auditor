from schemas import (
    MaterialProperties,
    SectionGeometry,
    Reinforcement,
    ShearReinforcement,
    InternalForces,
    TCVNAuditInput
)
from tcvn_engine import TCVNEngine

# Dữ liệu giả định (Mock Data)
mats = MaterialProperties(
    f_c=40.0, E_c=33000.0,
    f_y=420.0, E_s=200000.0,
    f_pu=1860.0, f_py=1674.0, E_p=197000.0, f_pe=1200.0
)

geom = SectionGeometry(
    h=2000.0, b=1500.0, b_w=250.0, h_f=200.0, A_g=750000.0, I_g=1e11
)

rebar_flex = Reinforcement(
    A_s=0.0, d_s=0.0,
    A_prime_s=0.0, d_prime_s=0.0,
    A_ps=3000.0, d_p=1850.0  # 30 cm2 cáp
)

rebar_shear = ShearReinforcement(
    A_v=226.0, s=200.0, alpha=90.0 # 2 nhánh D12
)

forces = InternalForces(
    M_u=7500.0, # 7500 kN.m
    V_u=1500.0, # 1500 kN
    N_u=0.0
)

audit_input = TCVNAuditInput(
    materials=mats,
    geometry=geom,
    flexural_rebar=rebar_flex,
    shear_rebar=rebar_shear,
    forces=forces
)

engine = TCVNEngine(audit_input)
result = engine.run_audit()

print("==== KẾT QUẢ KIỂM TOÁN ====")
print(f"Trạng thái tổng thể: {result.overall_status}")
print(f"Sức kháng Uốn: Capacity = {result.flexural.capacity:.2f} kNm, Demand = {result.flexural.demand:.2f} kNm ({result.flexural.is_passed})")
print(f"Sức kháng Cắt: Capacity = {result.shear.capacity:.2f} kN, Demand = {result.shear.demand:.2f} kN ({result.shear.is_passed})")
print("\n[Chi tiết]")
print(result.details.model_dump_json(indent=2))
