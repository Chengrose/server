from fastapi import APIRouter, Body, Depends, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, ValidationError
from datetime import timedelta
from .db import engine
from .models import *
from sqlmodel import Session, select
from typing import Annotated
import jwt, json
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, BASE_DIR

# 用户申请token时的校验信息
class StudentInfo(BaseModel):
    
    student_name: str
    student_number: str
    ip_address: str
    mac_address: str

class Submission(BaseModel):
    
    ip_address: str
    mac_address: str
    total_score: int
    experiment_id: int
    file_hash: str

def get_session():
    with Session(engine) as session:
        yield session
    
SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter()

# 根据学生id创建jwt
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# 解析 jwt 获取学生id
def deconde_token(token: str):
    print("---------------------------start decode token------------------")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as e:
        raise e
    except jwt.InvalidTokenError as e:
        raise e
    return payload["student_id"]

# 从提交请求中获得格式为mutipart/form-data中的请求体中的提交信息，将其转换为Submission对象进行检验
def parse_and_validate_submission(submission: Annotated[str, Form()]):
    try:
        submission = Submission(**json.loads(submission))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="提交的数据格式错误，请检查后重新提交！")
    
    return submission

# 从jwt中获取学生id，查找数据库获取对应学生信息
def get_user_from_token(x_token: Annotated[str, Header()]):
    print("---------------------------get token from headers------------------")
    student_id = deconde_token(x_token)
    if not student_id:
        raise HTTPException(status_code=401, detail="无效的token！")
    return student_id

# 由请求体中学生信息生成jwt
def get_access_token(student_info: StudentInfo, session: SessionDep):
    
    try:
        student = session.exec(select(Student).where(Student.student_number == student_info.student_number, Student.student_name == student_info.student_name)).one()
    except Exception as e:
        raise HTTPException(status_code=404, detail="输入学生信息不存在，请重新输入！若多次尝试后仍无结果，请向老师反映！")
    
    # 没有登录记录或者上一次登录记录与当前时间相差两小时以上
    if (not student.login_logs) or (datetime.now() - student.login_logs[0].login_time) >= timedelta(hours=2):
        return create_access_token({"student_id": student.student_id})
    else: 
        raise HTTPException(status_code=403, detail="两小时内已经获得过token，不可再获取！")
        
# 学生获取 jwt 接口
@router.post("/get-token")
async def get_token(token: Annotated[str, Depends(get_access_token)]):
    return {"token":token, "detail":"token获取成功，可开始实验！"}

# TODO 解析 jwt 用户信息，获取学生信息，校验hash是否一致
@router.post("/submit-result")
async def accept_result(student_id: Annotated[int, Depends(get_user_from_token)], submission: Annotated[Submission, Depends(parse_and_validate_submission)], report_file: UploadFile):
    upload_file_name = report_file.filename
    print(upload_file_name)
    submission = submission.model_dump()
    print(submission)
    with open(f"{BASE_DIR}/test_file/{upload_file_name}", "wb") as f:
        content = await report_file.read()
        f.write(content)
        
    return submission
    


