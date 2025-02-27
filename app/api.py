from fastapi import APIRouter, Body, Depends, Form, HTTPException, UploadFile
from pydantic import BaseModel
from datetime import timedelta
from .db import engine
from .models import *
from sqlmodel import Session, select
from typing import Annotated
import jwt

SECRET_KEY = "cfc886b7a95571cf8422587604527ef724be5f3d4940574e303da568179214f1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# 用户申请token时的校验信息
class StudentInfo(BaseModel):
    
    student_name: str
    student_number: str
    ip_address: str
    mac_address: str


def get_session():
    with Session(engine) as session:
        yield session
    
SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def get_access_token(student_info: StudentInfo, session: SessionDep):
    
    try:
        student = session.exec(select(Student).where(Student.student_number == student_info.student_number, Student.student_name == student_info.student_name)).one()
    except Exception as e:
        raise HTTPException(status_code=404, detail="输入学生信息不存在，请重新输入！若多次尝试后仍无结果，请向老师反映！")
    
    # 没有登录记录或者上一次登录记录与当前时间相差两小时以上
    if (not student.login_logs) or (datetime.now() - student.login_logs[0].login_time) >= timedelta(hours=2):
        return create_access_token({"student_number": student.student_number})
    else: 
        raise HTTPException(status_code=403, detail="两小时内已经获得过token，不可再获取！")
        
    
@router.post("/get-token")
async def get_token(token: Annotated[str, Depends(get_access_token)]):
    return {"token":token, "detail":"token获取成功，可开始实验！"}

# TODO 将文件上传到云端后存储到指定文件夹
@router.post("/submit-result")
async def accept_result(submission: Annotated[str, Form()], report_file: UploadFile):
    upload_file_name = report_file.filename
    print(upload_file_name)
    with open(f"./test_file/{upload_file_name}", "wb") as f:
        content = await report_file.read()
        f.write(content)
        
    return submission
    


