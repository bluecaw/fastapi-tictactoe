import random
from app.database import get_db_connection
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/guess", tags=["Number Guess"])

guess_state = {
    "target": random.randint(1, 100),
    "attempts": 0,
    "message": "1から100までの数字を入力してね！",
    "clear": False,
}


class GuessMove(BaseModel):
  number: int


@router.get("")
def get_game():
  return {
      "attempts": guess_state["attempts"],
      "message": guess_state["message"],
      "clear": guess_state["clear"],
  }


@router.post("/play")
def play_guess(move: GuessMove):
  if guess_state["clear"]:
    return guess_state

  guess_state["attempts"] += 1
  num = move.number

  if num < guess_state["target"]:
    guess_state["message"] = f"{num} より**もっと大きい**です！"
  elif num > guess_state["target"]:
    guess_state["message"] = f"{num} より**もっと小さい**です！"
  else:
    guess_state["message"] = (
        f"正解です！ 🎉 （試行回数: {guess_state['attempts']}回）"
    )
    guess_state["clear"] = True

    # 🎯 クリア時にSQLiteへスコアを保存
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO guess_scores (attempts) VALUES (?)",
        (guess_state["attempts"],),
    )
    conn.commit()
    conn.close()

  return guess_state


@router.get("/ranking")
def get_ranking():
  """過去のクリア記録（少い試行回数順の上位5件）を取得"""
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT attempts, created_at FROM guess_scores ORDER BY attempts ASC LIMIT"
      " 5"
  )
  rows = cursor.fetchall()
  conn.close()
  return [{"attempts": row["attempts"], "created_at": row["created_at"]} for row in rows]


@router.post("/reset")
def reset_game():
  guess_state["target"] = random.randint(1, 100)
  guess_state["attempts"] = 0
  guess_state["message"] = "1から100までの数字を当て直してね！"
  guess_state["clear"] = False
  return guess_state