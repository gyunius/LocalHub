# paste to backend/fts_setup.py and run: python backend/fts_setup.py
import sqlite3, pathlib
db=pathlib.Path('data/localhub.db').resolve()
conn=sqlite3.connect(db)
cur=conn.cursor()
cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS poi_fts USING fts5(contentid UNINDEXED, title, addr1, source_file, raw_json)")
cur.execute("DELETE FROM poi_fts")
cur.execute("INSERT INTO poi_fts(rowid, contentid, title, addr1, source_file, raw_json) SELECT rowid, contentid, title, addr1, source_file, raw_json FROM poi")
conn.commit(); conn.close()
print('FTS created/populated')