from .models import *
from sqlmodel import create_engine, Session


mysql_name = "sqlmodel"

mysql_url = f"mysql+mysqldb://root:123456@127.0.0.1:3306/{mysql_name}"

engine = create_engine(mysql_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def main():
    create_db_and_tables()
    
if __name__ == "__main__":
    main()