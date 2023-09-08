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
import asyncio
import httpx
import html
import json
import os
import openai
import time
import threading
from threading import Thread
from datetime import datetime
import urllib.request
import urllib.parse
from urllib.parse import urlencode
#파파고번역
import requests

router = APIRouter()
templates = Jinja2Templates(directory="templates") 

# 전역설정 load
BASE_DIR = os.getcwd() + "/conf"
ENV_CONF_FILE = os.path.join(BASE_DIR, 'env.json')
env_conf = json.loads(open(ENV_CONF_FILE).read())
auth = env_conf['AUTH']

BOT_URL = "https://api.telegram.org/bot" + auth['AISAYS_BOT'] + "/"

cmd = {
    "/start":["안녕하세요? 저는 @AISAYS_BOT 입니다.\n \
AiSays는 공개 질의응답 서비스입니다. \n \
자유롭게 질문하시면 AI(현 GPT-3) \n \
답변 후 URL을 생성해 드립니다. \n \
질의응답 내용은 웹(aisays.net)에 공개됩니다.",
              "이용 전 아래의 사항이 유의해 주세요. \n \
1. 연속대화 기능이 지원됩니다.(새로운 대화는 /new) \n \
2. 개인정보를 담은 질문은 피해주세요. \n \
본 서비스는 웹상에 질문과 답변이 공개됩니다.\n \
3. AI(GPT 등)의 자동답변은 정확성과 신뢰성이 보장되지 않습니다. \n \
재미나 참고용으로 이용해 주세요.",
              "기능 설명은 /help 를 입력해 주세요"
    ],
    "/help":["형식 없이 자유롭게 질문하시면 됩니다.\n \
별도의 태그를 지정하고 싶으신 경우, \n \
첫 줄에 '#'을 입력하시면 됩니다. \n \
예) \n \
\n \
#영어질문 \n \
'중요한건 꺾이지 않는 마음' 을 영어로?"   ,
"첫 줄에 다른 태그와 함께 '#md' 가 입력되면, \n \
질문 끝에 'use markdown.' 이 자동 입력됩니다. \n \
마크다운은 프로그램 코드 관련 질문에 유용합니다.\n \
예) \n \
#python #md \n \
파이썬 dict 사용법을 적어주세요.",
"첫 줄에 '#en' 이 입력되면, \n \
영어로 번역후 질문을 합니다. \n \
예) \n \
#en \n \
대한민국의 미래에 대해서 써줘."]
    ,
    "/new":["새로운 대화를 시작합니다."]
}

# 연속대화를 위한 리스트
myMessages = []

@router.post("/webhook", tags=["bot"])
async def webhook(req: Request):
    logger.debug("webhook")
    req_info = await req.json()
    logger.debug(req_info)
    message = None;
    edited_message = None;
    if 'message' in req_info:
        message = req_info['message']
    elif 'edited_message' in req_info:
        edited_message = req_info['edited_message']
    
    if message != None:
        chat_id = str(message['chat']['id'])
        text = message['text']
        logger.debug("----------------------------")
        logger.debug(chat_id)
        logger.debug(text)
        
        if text in cmd:
            if text == "/new":
                global myMessages
                myMessages = []  # 메시지 초기화
            for loop in range(len(cmd[text])):
                await sendMessage(chat_id, cmd[text][loop])
        elif text.startswith("/"):            
            await sendMessage(chat_id, "'/'로 시작하지만, 알수없는 명령어에요.")
        else:
            #await sendMessage(chat_id, text)
            sTime = datetime.now().strftime('%H:%M:%S')
            Thread(target=sendOpenai, args=(chat_id, text, sTime)).start()
            #await sendOpenai(chat_id, text, sTime)
        
    return {"result":"ok"}
    
    
def sendOpenai(chat_id, message, sTime):
    logger.debug("sendOpenai")
    ORG_ID = auth['OPENAI_ORG']
    API_KEY = auth['OPENAI_KEY']
    response = None
    callbackStatus = [True]
    
    max_tokens = 4000
    simple_tokens = 0
    
    # 제목 문자열 AI 전달 제외
    tagLines = []
    tagLine = None
    check_msg = message.split('\n')
    if len(check_msg) > 1:
        if check_msg[0].strip().startswith('#'):
            tagLine = check_msg[0]
            del check_msg[0]
    query_msg = "\n".join(check_msg)
    en_query_msg = None
    
    if len(check_msg) <= 1:
        if check_msg[0].startswith('#'):
            send(chat_id,"첫 줄에 # 태그 사용 시,\n두 줄 이상 입력하셔야 합니다.\n첫 줄은 제목으로, 두 번째 줄은 질문으로 적용됩니다.")
            return

    
    if tagLine is not None:
        tagLines = tagLine.split('#')
            
    # 마크다운 형식 요청 여부 확인
    for t in tagLines:
        if 'MD' == t.strip().upper():
            query_msg += "\n use markdown."
            break
            
    # 영어변환후 질문
    for t in tagLines:
        if 'EN' == t.strip().upper():
            en_query_msg = trans(query_msg)
            break
    
    if tagLine:
        logger.debug("T:"+tagLine)
        
    logger.debug("Q:"+query_msg)
    if en_query_msg:
        logger.debug("EnQ:"+en_query_msg)
    


    simple_tokens = len(query_msg.split(" ")) * 3
    logger.debug("---------------------------------------------")
    logger.debug("AI전송 문자열[%d]:%s"%(simple_tokens,query_msg))
    
    openai.organization = ORG_ID
    openai.api_key = API_KEY
    t = Thread(target=sendEx, args=("sendChatAction",chat_id,"typing",callbackStatus,10))
    t.daemon = True
    t.start()
    
    #await sendEx("sendChatAction",chat_id,"typing",callbackStatus)
    # text-moderation-playground
    # text-davinci-003

    # user message
    user_message = query_msg if en_query_msg is None else en_query_msg

    try:
        myMessages.append(
            {
                "role": "user",
                "content": user_message         
            })

        logger.debug(str(myMessages))

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=myMessages,
            temperature=0.3,
            max_tokens=3800,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None
            #stop=[" Human:", " AI:"]
        )
        logger.debug("get_gpt_response ok")
    except Exception as e:
        logger.debug("get_gpt_response err")
        logger.debug(response)
        logger.debug(e)
        #send(chat_id,"응답을 처리중가 발생하였습니다.\n %s"%e)
        send(chat_id,"응답을 처리중가 발생하였습니다.\n질문이 너무 길거나, 서버 과부하 일 수 있습니다.")
    finally:
        callbackStatus[0] = False
    
    logger.debug("response callbackStatus:"+str(callbackStatus))
    eTime = datetime.now().strftime('%H:%M:%S')
    
    myMessages.append(
        {
            "role": "assistant",
            "content": str(response.choices[0].message.content)         
        })

    logger.debug(str(response))
    logger.debug(str(response.choices[0].message.content))

    msg = f"[{sTime}] Q:{message} \n[{eTime}] A:\n{response.choices[0].message.content.strip()}"
    send(chat_id,msg)
    
    json_qna = {'id':response.id.strip(),
                'model':response.model.strip(),
                'prompt':message,
                'choice':response.choices[0].message.content.strip()
    }
    
    if en_query_msg is not None:
        json_qna['prompt'] += "\n"+en_query_msg
        json_qna['choice'] += "\n\n"+ trans(json_qna['choice'],'en','ko')
    
    # 포스팅 제외 태그 확인
    logger.debug(tagLines)
    for t in tagLines:
        if 'DNP' == t.strip().upper():
            send(chat_id,"포스팅 제외 질문 (#DNP, Do Not Post) url 생성없음.")
            return

    writePost(chat_id,json_qna)




async def sendMessage(chatId, msg):
    logger.debug("sendMessage")
    url = BOT_URL + 'sendMessage'
    data1 = {
      "chat_id": chatId,
      "text": msg,
      "parse_mode": "HTML"
    }
    logger.debug(url)
    r = httpx.post(url, data=data1)
    logger.debug(r)

def sendEx(api, chat_id, action,callbackStatus, max_loop=5):
    logger.debug("sendEx")
    txt = urllib.parse.quote_plus(action)
    rep = None

    url = BOT_URL
    url += api
    url += "?chat_id=" + chat_id
    url += "&action=" + action
    logger.debug(url)

    while callbackStatus[0]:
        max_loop -= 1
        if max_loop <= 0:
            logger.debug("while callbacksStgatue:loop over")
            break

        logger.debug("while callbacksStgatue[%d]:%s"%(max_loop,str(callbackStatus)))
        rep = urllib.request.urlopen(url)
        time.sleep(5)
        
    del callbackStatus


def send(chat_id, txt):
    logger.debug("send")
    txt = urllib.parse.quote_plus(txt)
    
    url = BOT_URL
    url += "sendmessage"
    url += "?chat_id=" + chat_id
    url += "&text=" + txt
    
    rep = urllib.request.urlopen(url)
    return rep.read()
    
def writePost(chat_id, json_qna):
    logger.debug("writePost")
    body = json_qna
    url = env_conf['SITE']+ "qna/"
    logger.debug(url)
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    logger.debug(jsondata)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)
    res_url = json.loads(response.read().decode('utf-8'))
    logger.debug("response="+res_url['result'])
    send(chat_id,res_url['result'])


# 파파고번역
def trans(query,slang=None,tlang=None):
    client_id = auth['PAPAGO_ID'] # 개발자센터에서 발급받은 Client ID 값
    client_secret = auth['PAPAGO_SEC'] # 개발자센터에서 발급받은 Client Secret 값
    url = "https://openapi.naver.com/v1/papago/n2mt"

    if slang is None:
        src_lang = detectLangs(query)
    else:
        src_lang = slang
        
    if tlang is None:
        trg_lang = 'en'
    else:
        trg_lang = tlang

    #요청 헤더
    req_header = {"X-Naver-Client-Id":client_id, "X-Naver-Client-Secret":client_secret}
    #요청 파라미터
    req_param = {"source":src_lang, "target":trg_lang, "text":query}

    logger.debug(req_param)
    res = requests.post(url,headers=req_header, data=req_param)

    #print(res.status_code, res.ok)
    try:
        if res.ok:
            trans_txt=res.json()['message']['result']['translatedText']
            return trans_txt
        else:
            return None
    except:
        return None
        

# 파파고언어감지
def detectLangs(query):
    client_id = auth['PAPAGO_ID'] # 개발자센터에서 발급받은 Client ID 값
    client_secret = auth['PAPAGO_SEC'] # 개발자센터에서 발급받은 Client Secret 값
    url = "https://openapi.naver.com/v1/papago/detectLangs"

    #요청 헤더
    req_header = {"X-Naver-Client-Id":client_id, "X-Naver-Client-Secret":client_secret}
    #요청 파라미터
    req_param = {"query":query}
    try:
        res = requests.post(url,headers=req_header, data=req_param)

        if res.ok:
            langCode=res.json()['langCode']
            return langCode
        else:
            return None
    except:
        return None
