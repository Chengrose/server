import os
import toml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

config = toml.load(os.path.join(BASE_DIR, "config.toml"))

# jwt配置
SECRET_KEY = config["jwt"]["key"]
ALGORITHM = config["jwt"]["algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = config["jwt"]["expire_minutes"]

# 数据库配置
DIALECT = config["db"]["dialect"]
DRIVER = config["db"]["driver"]
USERNAME = config["db"]["username"]
PASSWORD = config["db"]["password"]
HOST = config["db"]["host"]
PORT = config["db"]["port"]
DATABASE = config["db"]["database"]

DATABASE_URL = f"{DIALECT}+{DRIVER}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"


