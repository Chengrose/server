from sqlmodel import SQLModel, Field, Relationship, desc
from datetime import date, datetime
from sqlalchemy import Column, Text, DateTime, DECIMAL, JSON, UniqueConstraint
from decimal import Decimal


# 教师表
class Instructor(SQLModel, table=True):
    __tablename__ = "instructor"

    instructor_id: int | None = Field(default=None, primary_key=True)
    instructor_name: str = Field(max_length=50, index=True)
    email: str = Field(max_length=100, unique=True, index=True)
    phone: str | None = Field(default=None, max_length=20)
    department: str | None = Field(default=None, max_length=50, index=True)
    title: str | None = Field(default=None, max_length=50)
    office_location: str | None = Field(default=None, max_length=50)
    hire_date: date | None = None
    status: str = Field(default="active", max_length=20)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )

    classes: list["Class"] = Relationship(
        back_populates="instructor", cascade_delete=True
    )
    assignments: list["Assignment"] = Relationship(
        back_populates="instructor", cascade_delete=True
    )
    assignment_grades: list["AssignmentGrade"] = Relationship(
        back_populates="instructor", cascade_delete=True
    )


# 班级表
class Class(SQLModel, table=True):
    __tablename__ = "class"

    class_id: int | None = Field(default=None, primary_key=True)
    class_code: str = Field(index=True, max_length=20)
    class_name: str = Field(max_length=100)
    semester: str = Field(max_length=20)
    instructor_id: int = Field(
        foreign_key="instructor.instructor_id", ondelete="CASCADE"
    )
    max_students: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    credit_hours: int | None = None
    description: str | None = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="active", max_length=20)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )

    instructor: Instructor = Relationship(back_populates="classes")
    students: list["Student"] = Relationship(
        back_populates="myclass", cascade_delete=True
    )
    assignments: list["Assignment"] = Relationship(
        back_populates="myclass", cascade_delete=True
    )


# 学生表
class Student(SQLModel, table=True):
    __tablename__ = "student"

    student_id: int | None = Field(default=None, primary_key=True)
    student_name: str = Field(max_length=50, index=True)
    email: str = Field(max_length=100, unique=True, index=True)
    student_number: str = Field(max_length=20, unique=True, index=True)
    admission_year: int | None = None
    status: str = Field(default="active", max_length=20)
    date_of_birth: date | None = None
    address: str | None = Field(default=None, sa_column=Column(Text))
    password_hash: str = Field(max_length=255)
    class_id: int = Field(foreign_key="class.class_id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )

    myclass: Class = Relationship(back_populates="students")
    assignment_submissions: list["AssignmentSubmission"] = Relationship(
        back_populates="student", cascade_delete=True
    )
    student_grades: list["StudentGrade"] = Relationship(
        back_populates="student", cascade_delete=True
    )
    submission_security_logs: list["SubmissionSecurityLog"] = Relationship(
        back_populates="student", cascade_delete=True
    )
    login_logs: list["LoginLog"] = Relationship(
        back_populates="student",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": lambda: desc(LoginLog.login_time)},
    )


# 实验表
class Assignment(SQLModel, table=True):
    __tablename__ = "assignment"

    assignment_id: int | None = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="class.class_id", ondelete="CASCADE")
    title: str = Field(max_length=100)
    description: str | None = Field(default=None, sa_column=Column(Text))
    total_quizzes: int = 0
    points_possible: int
    weight_percentage: Decimal = Field(sa_column=Column(DECIMAL(4, 2)))
    start_date: datetime
    due_date: datetime
    status: str = Field(default="active", max_length=20)
    created_by: int = Field(foreign_key="instructor.instructor_id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )

    myclass: Class = Relationship(back_populates="assignments")
    instructor: Instructor = Relationship(back_populates="assignments")
    quizzes: list["Quizz"] = Relationship(
        back_populates="assignment", cascade_delete=True
    )
    assignment_submissions: list["AssignmentSubmission"] = Relationship(
        back_populates="assignment", cascade_delete=True
    )
    student_grades: list["StudentGrade"] = Relationship(
        back_populates="assignment", cascade_delete=True
    )
    assignment_grades: list["AssignmentGrade"] = Relationship(
        back_populates="assignment", cascade_delete=True
    )


# 习题表
class Quizz(SQLModel, table=True):
    __tablename__ = "quizz"

    quiz_id: int | None = Field(default=None, primary_key=True)
    assignment_id: int = Field(
        foreign_key="assignment.assignment_id", ondelete="CASCADE"
    )
    quiz_number: int
    title: str = Field(max_length=100)
    description: str | None = Field(default=None, sa_column=Column(Text))
    points_possible: int
    programming_language: str | None = Field(default=None, max_length=50)
    template_code: str | None = Field(default=None, sa_column=Column(Text))
    test_cases: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )

    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "quiz_number", name="uix_assignment_id_quiz_number"
        ),
    )

    assignment: Assignment = Relationship(back_populates="quizzes")


# 实验提交表
class AssignmentSubmission(SQLModel, table=True):
    __tablename__ = "assignment_submission"

    submission_id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", ondelete="CASCADE")
    assignment_id: int = Field(
        foreign_key="assignment.assignment_id", ondelete="CASCADE"
    )
    attempt_number: int
    total_score: Decimal = Field(sa_column=Column(DECIMAL(5, 2)))
    ip_address: str = Field(max_length=45)
    mac_address: str = Field(max_length=17)
    submission_status: str | None = Field(default=None, max_length=20)
    submitted_at: datetime = Field(default_factory=datetime.now)
    graded_at: datetime | None = None
    grade_hash_verified: bool = False
    grade_version_used: int | None = None

    student: Student = Relationship(back_populates="assignment_submissions")
    assignment: Assignment = Relationship(back_populates="assignment_submissions")
    student_grade: "StudentGrade" = Relationship(
        back_populates="best_submission", cascade_delete=True
    )
    submission_security_log: "SubmissionSecurityLog" = Relationship(
        back_populates="submission", cascade_delete=True
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "assignment_id",
            "attempt_number",
            name="uix_student_id_assignment_id_attempt_number",
        ),
    )


# 学生实验最终成绩表
class StudentGrade(SQLModel, table=True):
    __tablename__ = "student_grade"

    grade_id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(
        foreign_key="student.student_id", index=True, ondelete="CASCADE"
    )
    assignment_id: int = Field(
        foreign_key="assignment.assignment_id", index=True, ondelete="CASCADE"
    )
    final_score: Decimal = Field(sa_column=Column(DECIMAL(5, 2)))
    submission_count: int = 0
    best_submission_id: int = Field(
        foreign_key="assignment_submission.submission_id", ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )
    notes: str | None = Field(default=None, sa_column=Column(Text))

    student: Student = Relationship(back_populates="student_grades")
    assignment: Assignment = Relationship(back_populates="student_grades")
    best_submission: AssignmentSubmission = Relationship(back_populates="student_grade")

    __table_args__ = (
        UniqueConstraint(
            "student_id", "assignment_id", name="uix_student_id_assignment_id"
        ),
    )


# 实验文件内容表
class AssignmentGrade(SQLModel, table=True):
    __tablename__ = "assignment_grade"

    grade_id: int | None = Field(default=None, primary_key=True)
    assignment_id: int = Field(
        foreign_key="assignment.assignment_id", unique=True, ondelete="CASCADE"
    )
    file_name: str = Field(max_length=255)
    file_path: str = Field(max_length=255)
    file_hash: str = Field(max_length=128)
    file_size: int
    version: int = 1
    last_verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, onupdate=datetime.now)
    )
    created_by: int = Field(foreign_key="instructor.instructor_id", ondelete="CASCADE")

    assignment: Assignment = Relationship(back_populates="assignment_grades")
    instructor: Instructor = Relationship(back_populates="assignment_grades")
    submission_security_logs: list["SubmissionSecurityLog"] = Relationship(
        back_populates="grade"
    )


# 提交信息校验表
class SubmissionSecurityLog(SQLModel, table=True):
    __tablename__ = "submission_security_log"

    log_id: int | None = Field(default=None, primary_key=True)
    submission_id: int = Field(
        foreign_key="assignment_submission.submission_id",
        index=True,
        ondelete="CASCADE",
    )
    student_id: int = Field(
        foreign_key="student.student_id", index=True, ondelete="CASCADE"
    )
    grade_id: int = Field(foreign_key="assignment_grade.grade_id", ondelete="CASCADE")
    ip_address: str | None = Field(index=True)
    mac_address: str | None = None
    user_agent: str | None = Field(default=None, sa_column=Column(Text))
    geolocation: str | None = Field(default=None, sa_column=Column(Text))
    submission_timestamp: datetime = Field(default_factory=datetime.now, index=True)
    computed_hash: str = Field(max_length=256)
    grade_hash_valid: bool | None = None
    is_suspicious: bool = False
    suspicious_reason: str | None = Field(default=None, sa_column=Column(Text))
    notes: str | None = Field(default=None, sa_column=Column(Text))

    submission: AssignmentSubmission = Relationship(
        back_populates="submission_security_log"
    )
    student: Student = Relationship(back_populates="submission_security_logs")
    grade: AssignmentGrade = Relationship(back_populates="submission_security_logs")


class LoginLog(SQLModel, table=True):
    __tablename__ = "login_log"

    login_log_id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", ondelete="CASCADE")
    mac_address: str
    ip_address: str
    login_time: datetime = Field(default_factory=datetime.now)

    student: Student = Relationship(back_populates="login_logs")
