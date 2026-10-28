import sqlite3

DB_FILE = "game_scores.db"


def get_db_connection():
  conn = sqlite3.connect(DB_FILE)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  """アプリ起動時に全ゲーム用のテーブルを自動作成する"""
  conn = get_db_connection()
  cursor = conn.cursor()

  # 1. 数字当てゲーム用テーブル
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS guess_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempts INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  # 2. まるばつゲーム用テーブル
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS ttt_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  # 3. ドット＆ボックス用テーブル
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS dnb_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            p1_score INTEGER NOT NULL,
            p2_score INTEGER NOT NULL,
            winner TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  # 4. じゃんけん連勝バトル用テーブル
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS rps_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            streak INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  conn.commit()
  conn.close()