from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.logger import logger
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from aiomysql import Pool, DictCursor
from db.conn import get_db_conn
from datetime import date
from datetime import datetime
import markdown
import html
import json
import os
import xmltodict

#메모리 누수체크용
import gc
import tracemalloc
import psutil

#형태소 태깅
from kiwipiepy import Kiwi
from collections import Counter



router = APIRouter()
templates = Jinja2Templates(directory="templates") 

# 전역설정 load
BASE_DIR = os.getcwd() + "/conf"
ENV_CONF_FILE = os.path.join(BASE_DIR, 'env.json')
env_conf = json.loads(open(ENV_CONF_FILE).read())
PAGES = env_conf['PAGES']


# 메모리 누수체크용
process = psutil.Process(os.getpid())
tracemalloc.start()
s = None


@router.get('/robots.txt')
def robots():
    data = """
    User-agent: *
    Allow: /
    Sitemap: https://aisays.net/rss
    """
    return Response(content=data, media_type='text/plain')
"""
@router.get('/adx.txt')
def robots():
    data = ""
    return Response(content=data, media_type='text/plain')
"""

@router.get('/googleXXXXXXXXXXXXXXXX.html')
def google_domain_check():
    data = """
    google-site-verification: googleXXXXXXXXXXXXXXXX.html
    """
    return Response(content=data, media_type='text/plain')


# 메모리누수체크용(1)
@router.get('/memory')
def print_memory():
    return {'memory': process.memory_info().rss}

# 메모리누수체크용(2)
@router.get("/snapshot")
def snap():
    global s
    if not s:
        s = tracemalloc.take_snapshot()
        return "taken snapshot\n"
    else:
        lines = []
        top_stats = tracemalloc.take_snapshot().compare_to(s, 'lineno')
        for stat in top_stats[:10]:
            
            lines.append({"item":str(stat)})
        
        r = {}
        r['result'] = lines
        return r
        

# DB정규화
@router.get("/update_A#SDFSDF")
async def update(request: Request,db:Pool = Depends(get_db_conn)):
    logger.debug("update")
        
    # 최근글 5개
    sql = """
        SELECT * FROM  question
        WHERE prompt LIKE '#%'
    """
       
    insert_sql = """
        INSERT INTO qna.tags (seq,crdt,tag) 
        VALUES (%s,%s,%s)
    """
    
    update_sql = """
        UPDATE question
        SET prompt = %s
        WHERE seq = %s
    """
    
    cur  = await db.cursor(DictCursor)
    await cur.execute(sql)
    rows = await cur.fetchall()
    
    tmp_prompts = None
    tmp_tags = None
    tmp_tag = None
    for r in rows:
        tmp_prompts = r['prompt'].split('\n')
        
        if len(tmp_prompts) > 1:
            tmp_tags = tmp_prompts[0].split('#')
            del tmp_prompts[0]
            prompt = '\n'.join(tmp_prompts)
            logger.debug(prompt)
            await cur.execute(update_sql,(prompt,str(r['seq'])))
            
            for tmp_tag in tmp_tags:
                if tmp_tag:
                    await cur.execute(insert_sql,(str(r['seq']),r['crdt'],tmp_tag))
                
# 형태소 태깅 테스트
@router.get("/kiwi")
async def kiwi(request: Request,db:Pool = Depends(get_db_conn)):
    kiwi = Kiwi()
    """
    Parameters
    texts :Iterable[str]
        분석할 문자열의 리스트, 혹은 Iterable입니다.
    min_cnt :int
        추출할 단어의 최소 출현 빈도입니다. 이 빈도보다 적게 등장한 문자열은 단어 후보에서 제외됩니다.
    max_word_len :int
        추출할 단어 후보의 최대 길이입니다. 이 길이보다 긴 단어 후보는 탐색되지 않습니다.
    min_score :float
        단어 후보의 최소 점수입니다. 이 점수보다 낮은 단어 후보는 고려되지 않습니다. 이 값을 낮출수록 단어가 아닌 형태가 추출될 가능성이 높아지고, 반대로 이 값을 높일 수록 추출되는 단어의 개수가 줄어들므로 적절한 수치로 설정할 필요가 있습니다.
    pos_score :float
        단어 후보의 품사 점수입니다. 품사 점수가 이 값보다 낮은 경우 후보에서 제외됩니다.
    """
    test_str = """
    python anaconda 에서 자주 사용되면 명령어 목록을 설명과 함께 작성해줘. 
[23:12:11] A:
# Anaconda 명령어 목록

## conda

- `conda create`: 환경을 생성합니다.
- `conda env list`: 설치된 환경을 보여줍니다.
- `conda env remove`: 환경을 제거합니다.
- `conda install`: 패키지를 설치합니다.
- `conda list`: 설치된 패키지를 보여줍니다.
- `conda update`: 패키지를 업데이트합니다.
- `conda search`: 패키지를 검색합니다.

## pip

- `pip install`: 패키지를 설치합니다.
- `pip list`: 설치된 패키지를 보여줍니다.
- `pip search`: 패키지를 검색합니다.
- `pip uninstall`: 패키지를 제거합니다.
- `pip freeze`: 설치된 패키지의 버전을 보여줍니다.
    """
    #test_str = test_str.split("\n")
    logger.debug(test_str)
    
    #result = kiwi.extract_words(test_str, 2, 10, 0.01)
    result = kiwi.tokenize(test_str, normalize_coda=False)
    #logger.debug(result)
    
    results= []
    for token, pos, _, _ in result:
        if len(token) != 1 and pos.startswith('N') or pos.startswith('SL'):
            results.append(token)
    logger.debug(results)
    
    counter = Counter()
    
    #for token in results:
    counter.update(results)
    #ogger.debug(token)
        
    logger.debug(counter.most_common(5))
    
    

