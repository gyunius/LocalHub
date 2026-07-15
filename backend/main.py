from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
from datetime import datetime
import json

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from models import Base, POI, Post, Comment

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
DB_PATH = os.getenv("DB_PATH") or str(Path(__file__).parent / "data" / "localhub.db")
db_url = f"sqlite+aiosqlite:///{Path(DB_PATH).resolve().as_posix()}"

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

app = FastAPI(title="LocalHub API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def poi_to_dict(r: POI):
    return {
        "contentid": r.contentid,
        "region": r.region,
        "contenttypeid": r.contenttypeid,
        "title": r.title,
        "addr1": r.addr1,
        "addr2": r.addr2,
        "zipcode": r.zipcode,
        "tel": r.tel,
        "mapx": r.mapx,
        "mapy": r.mapy,
        "firstimage": r.firstimage,
        "firstimage2": r.firstimage2,
        "createdtime": r.createdtime,
        "modifiedtime": r.modifiedtime,
        "source_file": r.source_file,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }

@app.get("/api/pois")
async def list_pois(q: str | None = Query(None), region: str | None = None, contenttypeid: str | None = None, limit: int = 20, offset: int = 0):
    async with AsyncSessionLocal() as session:
        if q:
            # FTS search to get contentids
            sql = text("SELECT contentid FROM poi_fts WHERE poi_fts MATCH :q LIMIT :lim OFFSET :off")
            res = await session.execute(sql.bindparams(q=q, lim=limit, off=offset))
            contentids = [row[0] for row in res.fetchall()]
            if not contentids:
                return {"count": 0, "items": []}
            stmt = select(POI).where(POI.contentid.in_(contentids))
        else:
            stmt = select(POI)
            if region:
                stmt = stmt.where(POI.region == region)
            if contenttypeid:
                stmt = stmt.where(POI.contenttypeid == contenttypeid)
            stmt = stmt.limit(limit).offset(offset)

        res = await session.execute(stmt)
        rows = res.scalars().all()
        return {"count": len(rows), "items": [poi_to_dict(r) for r in rows]}

@app.get("/api/pois/{contentid}")
async def get_poi(contentid: str):
    async with AsyncSessionLocal() as session:
        poi = await session.get(POI, contentid)
        if not poi:
            raise HTTPException(status_code=404, detail="Not found")
        return poi_to_dict(poi)

@app.post("/api/pois/{contentid}/comments")
async def post_comment(contentid: str, comment_data: dict):
    async with AsyncSessionLocal() as session:
        poi = await session.get(POI, contentid)
        if not poi:
            raise HTTPException(status_code=404, detail="Not found")
        comment = Comment(**comment_data)
        session.add(comment)
        await session.commit()
        return {"message": "Comment added successfully", "comment_id": comment.id}

@app.post("/api/posts")
async def create_post(payload: dict = Body(...)):
    author = payload.get("author")
    password = payload.get("password")
    title = payload.get("title")
    body = payload.get("body")
    route = json.dumps(payload.get("route") or [], ensure_ascii=False)
    if not password or not title or not body:
        raise HTTPException(status_code=400, detail="password/title/body required")
    async with AsyncSessionLocal() as session:
        post = Post(author=author, password=password, title=title, body=body, route=route, ip=None)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return {"id": post.id, "created_at": post.created_at.isoformat()}

@app.get("/api/posts")
async def list_posts(limit: int = 20, offset: int = 0):
    async with AsyncSessionLocal() as session:
        stmt = select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        items = []
        for p in rows:
            items.append({
                "id": p.id,
                "author": p.author,
                "title": p.title,
                "route": json.loads(p.route) if p.route else [],
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        return {"count": len(items), "items": items}

@app.get("/api/posts/{post_id}")
async def get_post(post_id: int):
    async with AsyncSessionLocal() as session:
        p = await session.get(Post, post_id)
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "id": p.id,
            "author": p.author,
            "title": p.title,
            "body": p.body,
            "route": json.loads(p.route) if p.route else [],
            "created_at": p.created_at.isoformat() if p.created_at else None
        }

@app.put("/api/posts/{post_id}")
async def update_post(post_id: int, payload: dict = Body(...)):
    password = payload.get("password")
    if not password:
        raise HTTPException(status_code=400, detail="password required")
    async with AsyncSessionLocal() as session:
        p = await session.get(Post, post_id)
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        if not _check_password(p.password, password):
            raise HTTPException(status_code=403, detail="Forbidden")
        if payload.get("title"):
            p.title = payload.get("title")
        if payload.get("body"):
            p.body = payload.get("body")
        if "route" in payload:
            p.route = json.dumps(payload.get("route") or [], ensure_ascii=False)
        p.modified_at = datetime.utcnow()
        session.add(p)
        await session.commit()
        return {"ok": True}

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int, password: str = Query(...)):
    async with AsyncSessionLocal() as session:
        p = await session.get(Post, post_id)
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        if not _check_password(p.password, password):
            raise HTTPException(status_code=403, detail="Forbidden")
        await session.delete(p)
        await session.commit()
        return {"ok": True}

# Comments
@app.post("/api/posts/{post_id}/comments")
async def create_comment(post_id: int, payload: dict = Body(...)):
    author = payload.get("author")
    password = payload.get("password")
    body = payload.get("body")
    if not password or not body:
        raise HTTPException(status_code=400, detail="password/body required")
    async with AsyncSessionLocal() as session:
        parent = await session.get(Post, post_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Post not found")
        c = Comment(post_id=post_id, author=author, password=password, body=body, ip=None)
        session.add(c)
        await session.commit()
        await session.refresh(c)
        return {"id": c.id, "created_at": c.created_at.isoformat()}

@app.get("/api/posts/{post_id}/comments")
async def list_comments(post_id: int, limit: int = 100, offset: int = 0):
    async with AsyncSessionLocal() as session:
        stmt = select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        return {"count": len(rows), "items": [
            {"id": r.id, "author": r.author, "body": r.body, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows]}

@app.put("/api/comments/{comment_id}")
async def update_comment(comment_id: int, payload: dict = Body(...)):
    password = payload.get("password")
    if not password:
        raise HTTPException(status_code=400, detail="password required")
    async with AsyncSessionLocal() as session:
        c = await session.get(Comment, comment_id)
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        if not _check_password(c.password, password):
            raise HTTPException(status_code=403, detail="Forbidden")
        if payload.get("body"):
            c.body = payload.get("body")
        c.modified_at = datetime.utcnow()
        session.add(c)
        await session.commit()
        return {"ok": True}

@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: int, password: str = Query(...)):
    async with AsyncSessionLocal() as session:
        c = await session.get(Comment, comment_id)
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        if not _check_password(c.password, password):
            raise HTTPException(status_code=403, detail="Forbidden")
        await session.delete(c)
        await session.commit()
        return {"ok": True}

def _check_password(stored: str, provided: str) -> bool:
    return stored == provided