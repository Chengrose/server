from .models import *
from sqlmodel import create_engine, Session
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def main():
    create_db_and_tables()
    
if __name__ == "__main__":
    main()