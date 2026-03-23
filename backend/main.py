from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

from schemas import TCVNAuditInput
from tcvn_engine import TCVNEngine
from aashto_engine import AASHTOEngine
from eurocode_engine import EurocodeEngine
from report_generator import generate_report, convert_word_to_pdf
from ai_assistant import SmartAssistant, AIOptions

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Bridge Section Auditor Pro API", version="1.0.0")

@app.get("/")
async def root():
    return {"status": "online", "message": "Bridge Section Auditor Pro API is running!"}

# Mount thư mục báo cáo tĩnh
import os
os.makedirs("reports", exist_ok=True)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Thêm cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế nên giới hạn domain (e.g. localhost:5173, 5175)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

class AIRequest(BaseModel):
    provider: str
    api_key: str
    model_name: str
    user_question: str = ""
    audit_result: dict

@app.post("/api/audit")
async def run_audit(input_data: TCVNAuditInput):
    """
    Endpoint chính chạy lệnh kiểm toán. Phân loại theo tiêu chuẩn đã chọn.
    """
    try:
        # 1. Routing theo chuẩn
        std = input_data.standard.upper()
        if "TCVN" in std:
            engine = TCVNEngine(input_data)
        elif "AASHTO" in std:
            engine = AASHTOEngine(input_data)
        elif "EUROCODE" in std:
            engine = EurocodeEngine(input_data)
        else:
            raise HTTPException(status_code=400, detail=f"Không hỗ trợ tiêu chuẩn: {std}")
        
        # 2. Chạy thuật toán
        result = engine.run_audit()
        res_dict = result.model_dump()
        res_dict['input'] = input_data.model_dump() # Đính kèm Input vào dữ liệu để Jinja2 và Frontend render
        
        # 3. Trả Result về cho Giao diện dạng JSON
        # File Word không còn được sinh dư thừa ở bước này nữa.
        return {
            "status": "success",
            "data": res_dict
        }

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
import uuid

@app.post("/api/report")
async def create_and_download_report(format: str, payload: dict, background_tasks: BackgroundTasks):
    try:
        format = format.lower()
        std = payload.get('input', {}).get('standard', 'TCVN 11823:2017')
        
        os.makedirs("reports", exist_ok=True)
        file_id = str(uuid.uuid4())
        template_name = "tcvn_template.docx" if "TCVN" in std else ("eurocode_template.docx" if "EUROCODE" in std else "aashto_template.docx")
        temp_path = f"templates/{template_name}"
        
        docx_out = f"reports/{file_id}.docx"
        pdf_out = f"reports/{file_id}.pdf"
        
        if not os.path.exists(temp_path):
            raise HTTPException(500, f"Dữ liệu mẫu (Template) không tồn tại: {temp_path}")
            
        # Nạp tệp cho tạo tài liệu Docx
        from report_generator import generate_report, convert_word_to_pdf
        generate_report(payload, temp_path, docx_out)
        
        def remove_file(path: str):
            import time
            time.sleep(2) # Cho phép FastAPI stream xong và đóng File handle
            if os.path.exists(path):
                try: os.remove(path)
                except Exception as e:
                    print(f"Lỗi khóa I/O khi dọn rác: {e}")
                
        if format == 'pdf':
            convert_word_to_pdf(docx_out, "reports")
            background_tasks.add_task(remove_file, docx_out) # Clean up docx regardless
            if not os.path.exists(pdf_out):
                raise HTTPException(500, "Xảy ra lỗi Cấu hình Server (LibreOffice). Vui lòng tải bản Word hoặc liên hệ Admin.")
            
            background_tasks.add_task(remove_file, pdf_out)
            return FileResponse(pdf_out, media_type="application/pdf", filename=f"Audit_Report_{std}.pdf")
        else:
            background_tasks.add_task(remove_file, docx_out)
            return FileResponse(docx_out, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"Audit_Report_{std}.docx")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/explain")
async def get_ai_explanation(request: AIRequest):
    """
    Endpoint cung cấp tính năng Trợ lý AI giải thích kết quả.
    API Key nằm trong body request, xử lý trực tiếp trên RAM và hủy ngay khi trả KQ.
    """
    try:
        ai_ops = AIOptions(request.provider, request.api_key, request.model_name)
        assistant = SmartAssistant(ai_ops)
        
        explanation = assistant.generate_explanation(
            audit_results_dict=request.audit_result,
            user_question=request.user_question
        )
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Chạy server Local phục vụ cho UI
    uvicorn.run(app, host="127.0.0.1", port=8000)
