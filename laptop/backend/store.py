import sqlite3
import json

DB_PATH = 'detections.db'

class DetectionStore:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as con:
            con.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    data TEXT
                )
            ''')

    def add(self, detection: dict):
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                'INSERT INTO detections (timestamp, data) VALUES (?, ?)',
                (detection['timestamp'], json.dumps(detection))
            )
            con.execute('''
                DELETE FROM detections WHERE id NOT IN (
                    SELECT id FROM detections ORDER BY id DESC LIMIT ?
                )
            ''', (self.max_size,))

    def get_all(self) -> list:
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute(
                'SELECT id, data FROM detections ORDER BY id DESC'
            ).fetchall()
        result = []
        for row_id, data in rows:
            d = json.loads(data)
            d['id'] = row_id
            result.append(d)
        return result

    def get_latest(self) -> dict | None:
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute(
                'SELECT id, data FROM detections ORDER BY id DESC LIMIT 1'
            ).fetchone()
        if row is None:
            return None
        d = json.loads(row[1])
        d['id'] = row[0]
        return d

    def delete(self, detection_id: int):
        with sqlite3.connect(DB_PATH) as con:
            con.execute('DELETE FROM detections WHERE id = ?', (detection_id,))

    def clear(self):
        with sqlite3.connect(DB_PATH) as con:
            con.execute('DELETE FROM detections')
