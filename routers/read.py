# 질문을 받아서 응답해주는 모듈
# 1. 기간내에 동일한 질문이 있는 경우 조회 결과를 응답
# (1.1) 키워드가 일치하는 질문이 있을 경우 "유사질문 내역" 을 보여줌
# 2. 새로운 질문의 경우
# 2.1 응답을 준비중입니다. (1분 후에 확인 해보셔요.) 출력
# (2.2) 형태소 분석을 통해 키워드가 일치하는 질문이 있을 경우 "유사질문 내역" 을 보여줌
# 2.3 질문내용을 DB 저장
# 2.4 질문내용을 ChatGPT에게 요청


from fastapi import APIRouter, Request, Depends, HTTPException
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
import markdown
import html
import json
import os


router = APIRouter()
templates = Jinja2Templates(directory="templates") 

# 전역설정 load
BASE_DIR = os.getcwd() + "/conf"
ENV_CONF_FILE = os.path.join(BASE_DIR, 'env.json')
env_conf = json.loads(open(ENV_CONF_FILE).read())
PAGES = env_conf['PAGES']

class Q(BaseModel):
    model: Optional[str] = "text-davinci-003"
    prompt: str
    max_tokens: Optional[int]=16
    temperature:Optional[float]=1
    top_p:Optional[float]=1
    n:Optional[int]=1
    stream:Optional[bool]=False
    logprobs:Optional[int]=None
    stop:Optional[str]=None


async def askChatGPT():
    # 질문 insert
    # chatGPT 요청
    # 답변 insert
    pass
    
@router.get("/", tags=["read"])
async def get_home(request: Request,db:Pool = Depends(get_db_conn)):
    logger.debug("get_home")
    #return RedirectResponse(PAGES['HOME'])
    
    # 최근글 5개
    lastest_sql = """
    SELECT seq
         , DATE_FORMAT(STR_TO_DATE(crdt, '%Y%m%d'),'%Y-%m-%d ') crdt
         , prompt_255 FROM question
    ORDER BY crdt DESC, TIME DESC LIMIT 0, 5
    """
    cur  = await db.cursor(DictCursor)
    await cur.execute(lastest_sql)
    lastest = await cur.fetchall()
    
    # 추천글 5개
    recommended_sql = """
    select q.seq as seq
         , DATE_FORMAT(STR_TO_DATE(q.crdt, '%Y%m%d'),'%Y-%m-%d ') crdt
         , IFNULL(v.good,0) as good
         , q.prompt_255
    from question q
    left join 
    (
        select seq, crdt, sum(good) good
        from vote
        group by seq, crdt
    ) v
    on q.crdt = v.crdt and q.seq =  v.seq 
    order by good desc, v.crdt desc limit 0, 5
    """
    cur  = await db.cursor(DictCursor)
    await cur.execute(recommended_sql)
    recommend = await cur.fetchall()
    
    # 많이본글 5개
    most_viewed_sql = """
    SELECT seq
         , DATE_FORMAT(STR_TO_DATE(crdt, '%Y%m%d'),'%Y-%m-%d ') crdt
         , prompt_255 FROM question
    ORDER BY views DESC, TIME DESC LIMIT 0, 5
    """
    cur  = await db.cursor(DictCursor)
    await cur.execute(most_viewed_sql)
    viewed = await cur.fetchall()
    
    logger.debug(lastest)
    context = {}
    context["request"] = request
    context["result"] = {"title":"AiSays"}
    context["lastest"] = lastest
    context["recommend"] = recommend
    context["viewed"] = viewed
    return templates.TemplateResponse("home.html", context)
    
    

@router.get("/q/{question}/", tags=["read"])
async def get_question(question:str,q:Q):
    # 동일한 질문 답변 검색
    ## 있을 경우 검색결과 return
    # 동일한 질문 진행중인건 검색
    ## 있을 경우 진행상태 return
    ## 없을 경우 
    ### 요청완료 전송
    ### ChatGPT 요청전송
    logger.debug("get_question")

    return "test ok"



@router.post("/q/{question}/", tags=["read"])
async def post_question(question:str,q:Q):
    logger.debug("post_question")
    return jsonable_encoder(q)
    
@router.get("/q/test")
async def test(
        page    : int = 1,
        limit   : int = 10,
        db      : Pool = Depends(get_db_conn)
    ):
    logger.debug("test")
    offset    = (page-1)*limit
    cur       = await db.cursor(DictCursor)

    await cur.execute(f'SELECT * FROM question limit {offset}, 10')
    return await cur.fetchall()

    
@router.get("/{seq}/", tags=["read"], description="AI로 완성된 답변 내용을 보여준다")
async def get_question(
        request: Request,
        seq:str, 
        db:Pool = Depends(get_db_conn)
    ):
    logger.debug("get_question")
    if not seq.isdigit():
        return RedirectResponse(PAGES['NOT_FOUND'])
    
    # SQL 질의응답 내역 확인
    sql = """
        SELECT q.seq, q.crdt, q.id
            , TRIM(q.prompt_255) as prompt_255
            , TRIM(q.prompt) as prompt
            , TRIM(a.choice)  as choice
            , IFNULL(q.views,0) as views
        FROM qna.question q LEFT JOIN qna.answer a
        ON q.seq = a.seq
        WHERE q.seq = %s
    """
    cur  = await db.cursor(DictCursor)
    await cur.execute(sql, seq)
    row = await cur.fetchone()
    
    # 조회 결과가 없을 경우
    if row == None:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    elif row['choice'] == None:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
        
    logger.debug(row)
    
    # SQL 평판정보 조회
    sql2 = """
        SELECT SUM(good) good, SUM(bad) bad
        FROM qna.vote
        WHERE seq = %s
        GROUP BY seq
    """
    cur  = await db.cursor(DictCursor)
    await cur.execute(sql2, seq)
    row2 = await cur.fetchone()
    if row2 == None:
        row2 = {}
        row2['good'] = 0
        row2['bad'] = 0
    
    # 조회 결과가 있을 경우 조회수 증가
    await increase_in_views(cur,seq)
    
    # 태그 조회 (제목으로 사용)
    tag_sql ="""
        SELECT seq, tag FROM tags
        WHERE seq = %s
    """
    await cur.execute(tag_sql, seq)
    tags = await cur.fetchall()
    
    tags = ['#'+t['tag'].upper() for t in tags]
    title = ' '.join(tags)
    logger.debug(tags)
    
    prompt = row['prompt']

    logger.debug("-----------------------------------------")
    logger.debug(title)
    logger.debug(prompt)
    row['title'] = title
    row['prompt'] = prompt
    
    choice = row['choice']    

    # Dom Based XSS 방지
    try:
        safe_choice = html.escape(choice)
    except:
        logger.debug('escape 에러')
        pass


    # 코드 블럭이 있으면 md 적용
    if "```" in choice or "##" in choice:
        safe_choice = markdown.markdown(choice,extensions=['fenced_code'])



    row['choice'] = safe_choice
    
    #print(markdown.markdown(row['choice']))
    context = {}
    context["request"] = request
    context["seq"] = seq
    context["result"] = row
    context["vote"] = row2
    #print(row)

    #return "test ok"
    return templates.TemplateResponse("post.html", context)
    
async def increase_in_views(cur, seq):
    sql = """
        UPDATE qna.question q
        SET q.views = IFNULL(q.views,0)+1
        WHERE q.seq = %s
    """
    logger.debug("increase_in_views")
    await cur.execute(sql, (seq))
