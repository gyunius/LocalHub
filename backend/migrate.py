#!/usr/bin/env python3
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base, POI, Post, Comment

def make_db_url(db_path: Path) -> str:
    p = db_path.resolve()
    return f"sqlite+aiosqlite:///{p.as_posix()}"

async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def safe_float(v):
    try:
        return float(v) if v not in (None, "", "None") else None
    except Exception:
        return None

async def upsert_items(session: AsyncSession, items, source_file, limit=None):
    processed = 0
    for item in items:
        cid = str(item.get("contentid") or item.get("contentid") or "").strip()
        if not cid:
            continue
        existing = await session.get(POI, cid)
        mapx = safe_float(item.get("mapx"))
        mapy = safe_float(item.get("mapy"))
        raw = json.dumps(item, ensure_ascii=False)
        now = datetime.utcnow()

        if existing:
            existing.region = item.get("region") or existing.region
            existing.contenttypeid = item.get("contenttypeid") or existing.contenttypeid
            existing.title = item.get("title") or existing.title
            existing.addr1 = item.get("addr1") or existing.addr1
            existing.addr2 = item.get("addr2") or existing.addr2
            existing.zipcode = item.get("zipcode") or existing.zipcode
            existing.tel = item.get("tel") or existing.tel
            existing.mapx = mapx if mapx is not None else existing.mapx
            existing.mapy = mapy if mapy is not None else existing.mapy
            existing.firstimage = item.get("firstimage") or existing.firstimage
            existing.firstimage2 = item.get("firstimage2") or existing.firstimage2
            existing.createdtime = item.get("createdtime") or existing.createdtime
            existing.modifiedtime = item.get("modifiedtime") or existing.modifiedtime
            existing.raw_json = raw
            existing.source_file = source_file
            existing.ingested_at = now
            session.add(existing)
        else:
            poi = POI(
                contentid=cid,
                region=item.get("region"),
                contenttypeid=item.get("contenttypeid"),
                title=item.get("title"),
                addr1=item.get("addr1"),
                addr2=item.get("addr2"),
                zipcode=item.get("zipcode"),
                tel=item.get("tel"),
                mapx=mapx,
                mapy=mapy,
                firstimage=item.get("firstimage"),
                firstimage2=item.get("firstimage2"),
                createdtime=item.get("createdtime"),
                modifiedtime=item.get("modifiedtime"),
                raw_json=raw,
                source_file=source_file,
                ingested_at=now,
            )
            session.add(poi)

        processed += 1
        if limit and processed >= limit:
            break
    return processed

async def migrate(data_dir: Path, db_path: Path, dry_run=False, sample=None):
    db_url = make_db_url(db_path)
    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    await init_db(engine)

    files = sorted([p for p in Path(data_dir).glob("*.json") if p.is_file()])
    total = 0
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            try:
                payload = json.load(fh)
            except Exception as e:
                print(f"Failed to parse {f.name}: {e}")
                continue
        items = payload.get("items") or payload.get("data") or []
        if not items and isinstance(payload, dict):
            for v in payload.values():
                if isinstance(v, list):
                    items = v
                    break

        if not items:
            print(f"No items in {f.name}, skipping.")
            continue

        if dry_run:
            print(f"[dry-run] {f.name}: {len(items)} items")
            total += len(items)
            continue

        async with AsyncSessionLocal() as session:
            processed = await upsert_items(session, items, f.name, limit=sample)
            await session.commit()
            print(f"Processed {processed} items from {f.name}")
            total += processed

    await engine.dispose()
    print(f"Migration complete. Total processed: {total}")

def default_paths():
    here = Path(__file__).parent
    return (Path(os.getenv("DATA_DIR") or here / "data"),
            Path(os.getenv("DB_PATH") or here / "data" / "localhub.db"))

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", help="JSON files folder")
    parser.add_argument("--db-path", help="SQLite DB file path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample", type=int, help="limit items per file (test)")
    args = parser.parse_args()

    load_dotenv(dotenv_path=Path(__file__).parent / ".env")
    data_dir = Path(args.data_dir) if args.data_dir else Path(os.getenv("DATA_DIR") or Path(__file__).parent / "data")
    db_path = Path(args.db_path) if args.db_path else Path(os.getenv("DB_PATH") or Path(__file__).parent / "data" / "localhub.db")

    if not data_dir.exists():
        raise SystemExit(f"data-dir not found: {data_dir}")
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

    await migrate(data_dir, db_path, dry_run=args.dry_run, sample=args.sample)

if __name__ == "__main__":
    asyncio.run(main())