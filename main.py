from fastapi import FastAPI, Request, Depends
from fastapi.logger import logger
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import read,write,webhook,rss,root_file,sitemap
from db.conn import create_pool
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse



app = FastAPI(docs_url="/fastapi", redoc_url=None)

origins = ["*"]

origins = [
    "http://aisays.net:8000/",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates") 

app.mount("/static", StaticFiles(directory="static"), name="static") 
app.include_router(read.router)
app.include_router(write.router)
app.include_router(webhook.router)
app.include_router(rss.router)
app.include_router(root_file.router)
app.include_router(sitemap.router)

@app.on_event("startup")
async def startup():
    logger.debug("startup")
    app.state.db_pool = await create_pool()
    
@app.on_event("shutdown")
async def shutdown():
    logger.debug("shutdown")
    app.state.db_pool.close()

@app.middleware("http")
async def state_insert(request: Request, call_next):
    logger.debug("state_insert")
    request.state.db_pool   = app.state.db_pool
    request.state.db_conn   = await app.state.db_pool.acquire()
    response                = await call_next(request)
    return response
    

@app.exception_handler(404)
async def custom_404_handler(_, __):
    return FileResponse('./static/error/404.html')
    
"""
@app.get("/hello")
def hello():
    return {"message": "안녕하세요"}

@app.get("/items/{id}", response_class=HTMLResponse) 
async def read_item(request: Request, id: str): 
    logger.debug("test")
    return templates.TemplateResponse("item.html", {"request": request, "id":id}) 
"""    


        