from app.main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

@pytest.mark.parametrize("student_name, student_number, ip_address, mac_address, status_code, detail", [
    ("李明", "20250001", "192.168.0.101", "00:1A:2B:3C:4D:5E", 200, "token获取成功，可开始实验！"),
    ("玫瑰", "20250002", "192.168.2.4", "00:1A:2B:3C:4D:5E", 404, "输入学生信息不存在，请重新输入！若多次尝试后仍无结果，请向老师反映！"),
    ("张芳", "20250002", "192.168.0.102", "00:1A:2B:3C:4D:5E", 403, "两小时内已经获得过token，不可再获取！"),
])
def test_get_token(student_name, student_number, ip_address, mac_address, status_code, detail):
    
    data = {
        "student_name": student_name,
        "student_number": student_number,
        "ip_address": ip_address,
        "mac_address": mac_address,
    }
    
    response = client.post("/get-token", json=data)
    print(response.json())
    assert response.status_code == status_code
    assert response.json()["detail"] == detail
    
