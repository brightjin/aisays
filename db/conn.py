from fastapi.requests import Request
import json
import os

from aiomysql import Pool, DictCursor
from aiomysql.sa import Engine
import aiomysql

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.getcwd() + "/conf"
DB_CONF_FILE = os.path.join(BASE_DIR, 'db_conf.json')
db_conf = json.loads(open(DB_CONF_FILE).read())
DB = db_conf["DB"]

# 디비 쿼리를 위한 종속성 주입을 위한 함수
def get_db_conn(request: Request):
    pool = request.state.db_pool
    db = request.state.db_conn
    try:
        yield db
    finally:
        pool.release(db)
        
        
async def create_pool():
    pool = await aiomysql.create_pool(
        user         = DB['user'], 
        password     = DB['password'],
        host         = DB['host'],
        port         = DB['port'],
        db           = DB['database'],
        minsize      = 100,
        maxsize      = 100,
        pool_recycle = 3600,
        autocommit   = True
    )
    
    return pool

