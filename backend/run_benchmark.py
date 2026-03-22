import os
from schemas import (
    MaterialProperties, SectionGeometry, Reinforcement, 
    ShearReinforcement, InternalForces, TCVNAuditInput
)
from report_generator import generate_report
from tcvn_engine import TCVNEngine
from aashto_engine import AASHTOEngine
from eurocode_engine import EurocodeEngine

def run_benchmarks():
    print("=== BAT DAU CHAY BENCHMARK TIÊU CHUẨN ===")
    
    # Base Data
    mats = MaterialProperties(
        f_c=40.0, E_c=33000.0, f_y=420.0, E_s=200000.0,
        f_pu=1860.0, f_py=1674.0, E_p=197000.0, f_pe=1200.0
    )
    geom = SectionGeometry(
        h=2000.0, b=1500.0, b_w=250.0, h_f=200.0, A_g=750000.0, I_g=1e11
    )
    rebar_flex = Reinforcement(
        A_s=500.0, d_s=1900.0, A_prime_s=0.0, d_prime_s=0.0,
        A_ps=3000.0, d_p=1850.0
    )
    rebar_shear = ShearReinforcement(A_v=226.0, s=200.0, alpha=90.0)
    forces = InternalForces(M_u=8000.0, V_u=1200.0, N_u=0.0)

    os.makedirs('reports', exist_ok=True)
    
    # 1. TCVN Benchmark
    print("-> Đang chạy TCVN 11823:2017...")
    input_tcvn = TCVNAuditInput(
        standard="TCVN 11823:2017",
        materials=mats, geometry=geom, flexural_rebar=rebar_flex, 
        shear_rebar=rebar_shear, forces=forces
    )
    res_tcvn = TCVNEngine(input_tcvn).run_audit().model_dump()
    res_tcvn['input'] = input_tcvn.model_dump()
    generate_report(res_tcvn, 'templates/tcvn_template.docx', 'reports/Benchmark_TCVN.docx')

    # 2. AASHTO Benchmark
    print("-> Đang chạy AASHTO LRFD...")
    input_aashto = TCVNAuditInput(
        standard="AASHTO LRFD",
        materials=mats, geometry=geom, flexural_rebar=rebar_flex, 
        shear_rebar=rebar_shear, forces=forces
    )
    res_aashto = AASHTOEngine(input_aashto).run_audit().model_dump()
    res_aashto['input'] = input_aashto.model_dump()
    generate_report(res_aashto, 'templates/aashto_template.docx', 'reports/Benchmark_AASHTO.docx')

    # 3. Eurocode Benchmark
    print("-> Đang chạy Eurocode 2 (EN 1992-1-1)...")
    input_euro = TCVNAuditInput(
        standard="EUROCODE 2",
        materials=mats, geometry=geom, flexural_rebar=rebar_flex, 
        shear_rebar=rebar_shear, forces=forces
    )
    res_euro = EurocodeEngine(input_euro).run_audit().model_dump()
    res_euro['input'] = input_euro.model_dump()
    generate_report(res_euro, 'templates/eurocode_template.docx', 'reports/Benchmark_EUROCODE.docx')

    print("=== BENCHMARK HOÀN TẤT - KIỂM TRA THƯ MỤC /reports ===")

if __name__ == "__main__":
    run_benchmarks()
