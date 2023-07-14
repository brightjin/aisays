# aisays
OpenAI 연계 웹서비스 (Oracle Cloud Ubuntu 환경에서 테스트됨)

# 0. 실행 준비물
1. 파이썬 실행환경
2. Mysql
   - [테이블 스크립트](https://github.com/syschat0/aisays/tree/main/script/SQL)
3. Conf 설정
   - [설정위치](https://github.com/syschat0/aisays/tree/main/conf)
   - db_conf, env 설정
   - [OpenAI API Keys](https://platform.openai.com/account/api-keys)
   - [Telegram Bot ID, API keys](https://hzoo.tistory.com/87)
   - [네이버 파파고 API Keys](https://developers.naver.com/docs/papago/papago-nmt-overview.md#사전-준비-사항)

# 1. oracle cloud 네트워크 설정

# 2. ubuntu 방화벽 해제
```Shell
sudo iptables -I INPUT 5 -i ens3 -p tcp --dport 8000 -m state --state NEW,ESTABLISHED -j ACCEPT
```
# 3. python 설치
- 3.10.6
## 3.1 python venv 환경 생성
- {가상환경보관소} 경로 생성
- cd {가상환경보관소}
- python -m venv {프로젝트명}

## 3.2 python 가상환경 실행스크립트 생성
- source {가상환경보관소}/{프로젝트명}/bin/activate


## 3.3 fastapi 패키지 설치
```Shell
pip install fastapi
```
## 3.4 jinja2 패키지 설치
```Shell
 pip install jinja2
```  
## 3.5 aiofiles 패키지 설치
```Shell
pip install aiofiles # CSS파일 로딩
```

## 3.6 uvicorn 패키지 설치
```Shell
pip install uvicorn
```

### 3.6.1 uvicorn 실행스크립트 생성
- 가상환경 실행스크립트 실행
- cd {프로젝트경로}
- uvicorn main:app --reload --host=0.0.0.0 --workers=4


# 4. Mysql 관련 설정
## 4.1 oracle cloud 3306 포트 해제
## 4.2 ubuntu 방화벽 설정해제
```Shell
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 3306 -j ACCEPT
sudo netfilter-persistent save
```

## 4.3 mysql 외부접속 설정
```Shell
sudo mysql -u root -p
```
```SQL
mysql> CREATE USER 'root'@'%' IDENTIFIED BY '비밀번호';
mysql> GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
mysql> FLUSH PRIVILEGES;
mysql> exit
```

## 4.4 mysql config 설정
```Shell
sudo nano /etc/mysql/my.cnf
vi /etc/mysql/mysql.conf.d/mysqld.cnf 에서 bind-address 주석처리 or 0.0.0.0 허용
```

## 4.5 python 연계
```Shell
pip install pydantic
pip install SQLAlchemy
pip install mysql # 설치 에러시 아래 4.6 참고

pip install cryptography # mysql auth 관련 커넥션 오류 시
```

## 4.6 pip install mysql 설치 에러시 아래 라이브러리 설치
```Shell
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
```

## 4.7 추가적으로 설치해야할 python 패키지
```Shell
pip install aiomysql
pip install markdown
pip install httpx
pip install openai
pip install xmltodict
pip install psutil
pip install wheel
pip install kiwipiepy
```

## 4.8 설정변경
- {project}/conf/db.json
- DB 접속정보 설정

## 4.9 Table 생성
mysql console에서 아래 명령 실행
```SQL
mysql> source {aisays_home}/script/SQL/answer.sql
mysql> source {aisays_home}/script/SQL/question.sql
mysql> source {aisays_home}/script/SQL/tags.sql
mysql> source {aisays_home}/script/SQL/vote.sql
```

## 5. Telegram Bot
1. bot 생성
2. .../getMe
3. webhook 등록
```
https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://193.122.120.219:8000/static/webhook
```