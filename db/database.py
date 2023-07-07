from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_CONF_FILE = os.path.join(BASE_DIR, 'db_conf.json')
db_conf = json.loads(open(DB_CONF_FILE).read())
DB = db_conf["DB"]

DB_URL = f"mysql+pymysql://{DB['user']}:{DB['password']}@{DB['host']}:{DB['port']}/{DB['database']}?charset=utf8"

engine = create_engine(
    DB_URL, encoding = 'utf-8'
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engin)

Base = declarative_base()
