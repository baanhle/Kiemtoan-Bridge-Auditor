# Viết thuật toán tính toán theo chuẩn AASHTO LRFD 
from tcvn_engine import TCVNEngine
from schemas import TCVNAuditInput, TCVNAuditOutput

class AASHTOEngine(TCVNEngine):
    """
    Tiêu chuẩn AASHTO LRFD (Bản Metric) hoàn toàn tương đương với TCVN 11823:2017.
    Chỉ thiết lập class riêng biệt nhằm phục vụ cấu trúc rẽ nhánh xuất báo cáo và
    sẵn sàng cho các cập nhật độc lập của AASHTO (như LRFD 9th Edition).
    """
    def __init__(self, input_data: TCVNAuditInput):
        # Đè lại thẻ chuẩn thành AASHTO cho việc in báo cáo
        input_data.standard = "AASHTO LRFD"
        super().__init__(input_data)
        
    def run_audit(self) -> TCVNAuditOutput:
        """Kế thừa tính toán nhưng override nếu AASHTO có khác biệt ở version mới"""
        return super().run_audit()
