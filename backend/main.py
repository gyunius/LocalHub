from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from models import POI

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