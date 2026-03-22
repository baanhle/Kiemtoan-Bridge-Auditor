import os
from docxtpl import DocxTemplate

def generate_report(audit_result_dict: dict, template_path: str, output_path: str):
    """
    Hàm sinh báo cáo Word từ kết quả tính toán (audit_result_dict)
    và template file (.docx).
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Không tìm thấy template: {template_path}")
        
    doc = DocxTemplate(template_path)
    doc.render(audit_result_dict)
    doc.save(output_path)
    print(f"✅ Báo cáo Word đã được xuất thành công tại: {output_path}")

def convert_word_to_pdf(word_path: str, output_dir: str):
    """
    Sử dụng docx2pdf ưu tiên trên Windows để đảm bảo font chuẩn Microsoft.
    Fallback sang LibreOffice headless.
    """
    import os
    import platform
    import subprocess
    
    # Target PDF file path
    pdf_path = os.path.join(output_dir, os.path.basename(word_path).replace('.docx', '.pdf'))
    
    # Option 1: Try docx2pdf under Windows directly
    if platform.system() == "Windows":
        try:
            from docx2pdf import convert
            convert(word_path, pdf_path)
            print(f"✅ Đã convert sang PDF (MS Word Engine) lưu tại: {pdf_path}")
            return
        except Exception as e:
            print(f"⚠️ Lỗi convert docx2pdf: {e}, đang fallback lại LibreOffice...")

    # Option 2: Fallback LibreOffice
    sofc = "soffice"
    if platform.system() == "Windows":
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in paths:
            if os.path.exists(p):
                sofc = p
                break
                
    cmd = [
        sofc,
        "--headless",
        "--convert-to",
        "pdf",
        word_path,
        "--outdir",
        output_dir
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Đã convert sang PDF (LibreOffice) lưu tại: {output_dir}")
    except Exception as e:
        print(f"⚠️ Lỗi khi convert PDF: Bỏ qua bước này. Đảm bảo bạn đã cài MS Word hoặc LibreOffice. Lỗi: {e}")

# Đoạn mã Test chạy thử Pipeline xuất báo cáo
if __name__ == "__main__":
    from test_engine import engine, audit_input
    
    res = engine.run_audit()
    res_dict = res.model_dump()
    res_dict['input'] = audit_input.model_dump() # Bơm input vào payload cho Jinja2
    
    os.makedirs('reports', exist_ok=True)
    out_docx = 'reports/KetQua_TCVN.docx'
    
    generate_report(res_dict, 'templates/tcvn_template.docx', out_docx)
    convert_word_to_pdf(out_docx, 'reports')
