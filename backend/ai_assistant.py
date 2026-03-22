import os
import re

class AIOptions:
    def __init__(self, provider: str, api_key: str, model_name: str = "default"):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name

class SmartAssistant:
    """
    Module giao tiếp với AI (OpenAI, Gemini, Claude)
    Mục đích: Giải thích các thông số vật lý cho kỹ sư mà KHÔNG CHUỘT BẠCH làm toán.
    Policy: Runtime only (API Key không bao giờ bị ghi ra đĩa).
    """
    def __init__(self, ai_options: AIOptions):
        self.options = ai_options
        self.system_prompt = (
            "Bạn là một kỹ sư cầu đường thâm niên. Nhiệm vụ của bạn là giải thích ngắn gọn, "
            "dễ hiểu về nguyên nhân ĐẠT hoặc KHÔNG ĐẠT của mặt cắt bê tông cốt thép dự ứng lực. "
            "KHÔNG TỰ Ý THAY ĐỔI CÔNG THỨC HOẶC TÍNH TOÁN LẠI SỐ LIỆU. Chỉ nhận xét dựa trên Input."
        )

    def generate_explanation(self, audit_results_dict: dict, user_question: str = "") -> str:
        """Sinh phân tích chuyên sâu cho kết quả kiểm toán"""
        # Trích xuất dữ liệu cốt lõi để "mớm" vào Prompt
        overall = audit_results_dict.get('overall_status', 'N/A')
        flex = audit_results_dict.get('flexural', {})
        shear = audit_results_dict.get('shear', {})
        
        context_prompt = f"""
        Kết quả kiểm toán mặt cắt cầu: Trạng thái tổng thể = {overall}.
        Sức kháng uốn: Tỷ số Demand/Capacity = {flex.get('ratio', 0):.2f}. (Capacity: {flex.get('capacity', 0):.2f})
        Sức kháng cắt: Tỷ số Demand/Capacity = {shear.get('ratio', 0):.2f}. (Capacity: {shear.get('capacity', 0):.2f})
        """
        
        if user_question:
            context_prompt += f"\nCâu hỏi từ kỹ sư: {user_question}"
        else:
            if overall == "KHÔNG ĐẠT":
                context_prompt += "\nHãy phân tích nhanh nguyên nhân không đạt và gợi ý cách tăng cường tiết diện (thêm thép, tăng kích thước, v.v)."
            else:
                context_prompt += "\nHãy nhận xét về tính an toàn và mức độ tối ưu vật liệu dựa trên các tỷ số ở trên."

        full_prompt = f"{self.system_prompt}\n\nMỤC TIÊU PHÂN TÍCH:\n{context_prompt}"
        
        # Bắt đầu gọi API tương ứng (Mock functions for v1)
        if self.options.provider == "openai":
            return self._call_openai(full_prompt)
        elif self.options.provider == "gemini":
            return self._call_gemini(full_prompt)
        elif self.options.provider == "claude":
            return self._call_claude(full_prompt)
        else:
            return "Trợ lý AI đang đi uống cà phê. Vui lòng chọn đúng Provider nha Sếp!"

    def _call_openai(self, prompt: str) -> str:
        # Giả lập call API (Tránh throw lỗi khi thiếu package openai)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.options.api_key)
            model = self.options.model_name if self.options.model_name != "default" else "gpt-4o"
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3 # Độ sáng tạo thấp -> tính chính xác kỹ thuật cao
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Lỗi kết nối OpenAI: {str(e)}"

    def _call_gemini(self, prompt: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.options.api_key)
            model_name = self.options.model_name if self.options.model_name != "default" else "gemini-1.5-pro"
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Lỗi kết nối Gemini: {str(e)}"
            
    def _call_claude(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.options.api_key)
            model = self.options.model_name if self.options.model_name != "default" else "claude-3-5-sonnet-20240620"
            message = client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
             return f"⚠️ Lỗi kết nối Claude: {str(e)}"

if __name__ == "__main__":
    print("Testing AI Assistant Module...")
    # Không cung cấp Key thật để kiểm tra luồng
    ai_ops = AIOptions("openai", "sk-fake-key", "gpt-4o")
    assistant = SmartAssistant(ai_ops)
    print(assistant.generate_explanation({'overall_status': 'KHÔNG ĐẠT'}, "Tại sao lại trượt Uốn?"))
