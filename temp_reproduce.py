import math

def calculate(n_tendons, n_strands, area_per_strand):
    # Fixed parameters
    f_c = 35
    beta1 = 0.85 - 0.05 * ((f_c - 28.0) / 7.0)
    beta1 = max(0.65, min(0.85, beta1))
    
    f_pu = 1860
    f_py = 1674
    k = 0.28 # Low relaxation
    
    b = 1500
    b_w = 400
    h_f = 250
    h = 2000
    eccentricity = 850
    d_p = h - eccentricity
    
    A_ps = n_tendons * n_strands * area_per_strand
    
    # 1. c calculation (Rect assumption)
    numerator_rect = (A_ps * f_pu)
    denominator_rect = (0.85 * f_c * beta1 * b) + (k * A_ps * f_pu / d_p)
    c = numerator_rect / denominator_rect
    a = beta1 * c
    
    is_t = False
    if a > h_f:
        is_t = True
        numerator_t = (A_ps * f_pu) - (0.85 * f_c * (b - b_w) * h_f)
        denominator_t = (0.85 * f_c * beta1 * b_w) + (k * A_ps * f_pu / d_p)
        c = numerator_t / denominator_t
        a = beta1 * c
        
    f_ps = f_pu * (1 - k * (c / d_p))
    
    if not is_t:
        M_n = (A_ps * f_ps * (d_p - a/2))
    else:
        M_n = (A_ps * f_ps * (d_p - a/2) + 0.85 * f_c * (b - b_w) * h_f * (a/2 - h_f/2))
        
    return M_n * 1e-6, a, c, f_ps, is_t

print(f"{'Tendons':<10} {'Mn (kNm)':<15} {'a (mm)':<10} {'fps (MPa)':<15} {'Is_T':<10}")
for n in range(12, 0, -1):
    mn, a, c, fps, it = calculate(n, 19, 140)
    print(f"{n:<10} {mn:<15.2f} {a:<10.2f} {fps:<15.2f} {it:<10}")
