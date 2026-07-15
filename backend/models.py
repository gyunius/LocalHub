from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, Text, DateTime, Integer, ForeignKey
from datetime import datetime

Base = declarative_base()

class POI(Base):
    __tablename__ = "poi"

    contentid = Column(String, primary_key=True)
    region = Column(String, index=True)
    contenttypeid = Column(String, index=True)
    title = Column(String, index=True)
    addr1 = Column(String)
    addr2 = Column(String)
    zipcode = Column(String)
    tel = Column(String)
    mapx = Column(Float)
    mapy = Column(Float)
    firstimage = Column(String)
    firstimage2 = Column(String)
    createdtime = Column(String)
    modifiedtime = Column(String)
    raw_json = Column(Text)
    source_file = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String, index=True)               # 작성자 아이디(자유 입력)
    password = Column(String, nullable=False)         # 평문 저장(요청하신 대로)
    title = Column(String, nullable=False, index=True)
    body = Column(Text, nullable=False)
    route = Column(Text)    # JSON-직렬화된 POI contentid 리스트
    ip = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True, nullable=False)
    author = Column(String, index=True)
    password = Column(String, nullable=False)         # 평문 저장
    body = Column(Text, nullable=False)
    ip = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime)

