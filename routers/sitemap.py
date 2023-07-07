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

router = APIRouter()
templates = Jinja2Templates(directory="templates") 

# 전역설정 load
BASE_DIR = os.getcwd() + "/conf"
ENV_CONF_FILE = os.path.join(BASE_DIR, 'env.json')
env_conf = json.loads(open(ENV_CONF_FILE).read())
PAGES = env_conf['PAGES']


@router.get("/sitemap.xml", tags=["read"])
async def get_rss(request: Request,db:Pool = Depends(get_db_conn)):
    logger.debug("get_rss")
    max_count = 200
    rss_sql = """
    SELECT q.seq, q.crdt, q.time, q.id, LEFT(q.prompt,80) prompt, LEFT(choice,80) choice
    FROM qna.question q LEFT JOIN qna.answer a
    ON q.id = a.id
    ORDER BY q.crdt DESC, q.time DESC
    LIMIT 0, %s
    """
    
    cur  = await db.cursor(DictCursor)
    await cur.execute(rss_sql,max_count)
    rss = await cur.fetchall()
    
    db_date_format =  '%Y%m%d%H%M%S'
    rss_date_format = '%a, %d %b %Y %H:%M:%S %z'
    dt_obj = None
    
    sitemap_layout = {
        'urlset':{
            '@xmlns':'http://www.sitemaps.org/schemas/sitemap/0.9'
        }
    }
    
    urls = []
    url = {}
    for i in rss:
        try:
            dt_obj = datetime.strptime(i['crdt']+i['time'],db_date_format)
        except:
            dt_obj = datetime.now()
            
        url = {}
        url['loc'] = env_conf['SITE']+str(i['seq'])
        url['lastmod'] = datetime.strftime(dt_obj,rss_date_format)
       
        urls.append(url)
    
    
    sitemap_layout['urlset']['url'] = urls
    #xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml = xmltodict.unparse(sitemap_layout, pretty=True)
    
    return Response(content=xml, media_type="application/xml")