import jwt, json
import os
from fastapi import APIRouter, Body, Depends, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
from datetime import timedelta, timezone
from app.db import engine
from app.models import *
from sqlmodel import Session, select
from typing import Annotated
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, BASE_DIR

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
    assignment_number: int
    file_hash: str
    

def get_session():
    with Session(engine) as session:
        yield session
    
SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter()

# 根据学生id创建jwt
def create_access_token(data: dict):
    to_encode = data.copy()
    # 设置过期时间， 过期时间为utc时区时间，解析时会获取当前utc时间对比，使用本地时间会与预期不同
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# 解析jwt获取负载
def deconde_token(token: str):
    print("---------------------------start decode token------------------")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="token已过期，请重新获取！")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=400, detail="token格式错误！")

# 从提交请求中获得格式为mutipart/form-data中的请求体中的提交信息，将其转换为Submission对象进行检验
def parse_and_validate_submission(submission: Annotated[str, Form()]):
    try:
        submission = Submission(**json.loads(submission))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="提交的数据格式错误，请检查后重新提交！")
    
    return submission

# 从token负载中获取学生id，查找数据库获取对应学生信息
def get_user_from_token(x_token: Annotated[str, Header()], session: SessionDep):
    print("---------------------------get token from headers------------------")
    # 从负载中取得学生id
    student_id = deconde_token(x_token)["student_id"]
    statement = select(Student).where(Student.student_id == student_id)
    student = session.exec(statement).one()
    return student

# 由请求体中学生信息生成jwt
def get_access_token(student_info: StudentInfo, session: SessionDep):
    
    student = session.exec(
        select(Student).where(
            Student.student_number == student_info.student_number,
            Student.student_name == student_info.student_name
        )
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="输入学生信息不存在，请重新输入！若多次尝试后仍无结果，请向老师反映！")
    
    now = datetime.now()
    
    # 获取最近一次登录记录
    last_login_log = (
        session.exec(
            select(LoginLog)
            .join(Student)
            .where(Student.student_id == student.student_id)
            .order_by(LoginLog.login_time.desc())
            .limit(1)
        ).first()
    )
    
    # 没有登录记录或者上一次登录记录与当前时间相差两小时以上
    if (not last_login_log) or (now - last_login_log.login_time) >= timedelta(hours=2):
        
        # 向数据库中插入登录记录
        loginglog = LoginLog(
            student_id = student.student_id,
            mac_address = student_info.mac_address,
            ip_address = student_info.ip_address
        )
        
        try:
            session.add(loginglog)
            session.commit()
            session.refresh(loginglog)
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="数据库操作失败！")
        
        return create_access_token({"student_id": student.student_id})
    else: 
        raise HTTPException(status_code=403, detail="两小时内已经获得过token，不可再获取！")

# 学生获取 jwt 接口
@router.post("/get-token")
async def get_token(token: Annotated[str, Depends(get_access_token)]):
    return {"token":token, "detail":"token获取成功，可开始实验！"}

# TODO 存储学生
@router.post("/submit-result")
async def accept_result(
    student: Annotated[Student, Depends(get_user_from_token)],
    submission: Annotated[Submission, Depends(parse_and_validate_submission)],
    report_file: UploadFile,
    session: SessionDep
):

    statement = (
        select(AssignmentGrade.file_hash)
        .join(Assignment)
        .where(Assignment.assignment_number == submission.assignment_number)
    )

    # 实验文件对应的hash
    file_hash = session.exec(statement).first()

    # 校验测试文件hash
    print("submission用户提交内容:\n" + submission.model_dump_json(indent=4))

    # 比较提交的hash与数据库hash，若结果不匹配则抛出错误
    if (file_hash != submission.file_hash):
        
        # TODO 测试返回文件渲染到jupyter端
        return FileResponse(path=f"{BASE_DIR}/app/main.py", status_code=200, filename="main.py")

    upload_file_name = report_file.filename
    print("文件名称: " + upload_file_name)
    # submission = submission.model_dump()
    # print(submission)
    file_path = f"{BASE_DIR}/test_file/{student.myclass.class_name}/{upload_file_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(f"{BASE_DIR}/test_file/{student.myclass.class_name}/{upload_file_name}", "wb") as f:
        content = await report_file.read()
        f.write(content)

    return student