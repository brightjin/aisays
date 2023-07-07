from fastapi import APIRouter, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi.logger import logger
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from aiomysql import Pool, DictCursor
from db.conn import get_db_conn
from datetime import date
from datetime import datetime
import markdown
import html



router = APIRouter()
templates = Jinja2Templates(directory="templates") 

class QNA(BaseModel):
    #Common
    crdt: Optional[str] = None
    id:str
    #Q
    model: Optional[str] = "text-davinci-003"
    prompt:str
    #A
    choice:str

class VOTE(BaseModel):
    seq:int
    vote:bool

    
    
    
    


@router.post("/vote/", description="좋아요 or 나빠요")
async def vote(vote:VOTE, request: Request, db:Pool = Depends(get_db_conn)):
    vote = vote.dict()
    cur  = await db.cursor(DictCursor)
    logger.debug("-1----------------------------------------------")
    logger.debug(vote)
    logger.debug(request.headers.get('x-real-ip'))
    real_ip = request.headers.get('x-real-ip')
    
    # 게시물 유효성 조회
    inq_sql = """
        SELECT q.seq, q.crdt, q.id, IFNULL(good,0) good, IFNULL(bad,0) bad
        FROM qna.question q 
        LEFT JOIN qna.answer a
            ON q.seq = a.seq
        LEFT JOIN (
            SELECT v.seq, v.good, v.bad
            FROM qna.vote v
            WHERE v.seq = %s
             AND v.ip = %s
        ) v
        ON q.seq = v.seq
        WHERE q.seq = %s
    """
    await cur.execute(inq_sql,(vote['seq'],real_ip,vote['seq']))
    row = await cur.fetchone()
    logger.debug("-2----------------------------------------------")
    logger.debug(row)
    if row == None:
        return {"result":"Page not found."}
        
    if (row['good']+row['bad']) != 0:
        return {"result":"You have already voted."}
    
    # 평판 등록
    ins_sql = """
    	INSERT INTO qna.vote (seq,crdt,id,ip,good,bad)
        VALUES(%s,%s,%s,%s,%s,%s)
    """
    await cur.execute(ins_sql,
                    (row['seq'],
                     row['crdt'],
                     row['id'],
                     real_ip,
                     1 if vote['vote'] else 0,
                     0 if vote['vote'] else 1,))
    logger.debug("-3----------------------------------------------")
    # 평판 결과 조회
    vot_sql = """
        SELECT SUM(good) good, SUM(bad) bad
        FROM qna.vote
        WHERE seq = %s
        GROUP BY seq
    """
    await cur.execute(vot_sql,(vote['seq']))
    logger.debug("-4----------------------------------------------")
    row = await cur.fetchone()
    
    return {"result":"Voting completed.","good":row["good"],"bad":row["bad"]}
    
# 질문답변을 한번에 저장
@router.post("/qna/", description="질의응답을 저장하기 위한 API")
async def setQnA(qna:QNA, request: Request, db:Pool = Depends(get_db_conn)):
    now = datetime.now()
    now_date = now.strftime('%Y%m%d')
    now_time = now.strftime('%H%M%S')
    domain_name = request.headers.get('Host')
    seq = None
    tags = []
    prompt = None
    qna = qna.dict()
    cur  = await db.cursor(DictCursor)
    
    if qna['crdt'] is None:
        qna['crdt'] = now_date
    
    prompt = qna['prompt']
    
    lines = qna['prompt'].split('\n')
    logger.debug(lines[0])
    if len(lines) > 1:
        if lines[0].startswith('#'):
            tags = lines[0].split('#')
            del lines[0]
            prompt = '\n'.join(lines)
            
    query= """
        INSERT INTO qna.question (crdt, time, id, model, prompt_255, prompt) 
            values(%s,%s,%s,%s,%s,%s)
    """
    print(query%(qna['crdt'],now_time,qna['id'],qna['model'],prompt[:255],prompt))
    await cur.execute(query,(qna['crdt'],now_time,qna['id'],qna['model'],prompt[:255],prompt))
    seq = cur.lastrowid
    
    query= """
        INSERT INTO qna.answer (seq, crdt, id, choice) 
            values(%s,%s,%s,%s)
    """
    await cur.execute(query,(seq,qna['crdt'],qna['id'],qna['choice']))
    
    query= """
        SELECT MAX(seq) as seq FROM qna.question
    """
    await cur.execute(query)
    result = await cur.fetchone()
    
    url = "https://"+domain_name +"/"+str(result["seq"]) # url 변경필요
    
    
    tag_insert_sql = """
        INSERT INTO qna.tags (seq,crdt,tag) 
        VALUES (%s,%s,%s)
    """
    for tmp_tag in tags:
        if tmp_tag:
            await cur.execute(tag_insert_sql,(str(seq),qna['crdt'],tmp_tag))
    
    return {"result":url}


