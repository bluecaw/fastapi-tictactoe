import sqlite3

DB_FILE = "game_scores.db"


def get_db_connection():
  """データベースへの接続を取得する（辞書型風にアクセスできるように設定）"""
  conn = sqlite3.connect(DB_FILE)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  """アプリ起動時にテーブルを自動作成する"""
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS guess_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempts INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()