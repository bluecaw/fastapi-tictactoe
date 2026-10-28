from app.database import get_db_connection
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/ttt", tags=["Tic-Tac-Toe"])

ttt_state = {"board": [""] * 9, "turn": "X", "winner": None}


class TTTMove(BaseModel):
  index: int

@router.get("/history")
def get_ttt_history():
  """直近5件の対戦結果を取得"""
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT winner, created_at FROM ttt_scores ORDER BY id DESC LIMIT 5"
  )
  rows = cursor.fetchall()
  conn.close()
  return [
      {"winner": row["winner"], "created_at": row["created_at"]} for row in rows
  ]


@router.get("")
def get_game():
  return ttt_state


def check_winner(board):
  lines = [
      [0, 1, 2],
      [3, 4, 5],
      [6, 7, 8],
      [0, 3, 6],
      [1, 4, 7],
      [2, 5, 8],
      [0, 4, 8],
      [2, 4, 6],
  ]
  for line in lines:
    a, b, c = line
    if board[a] and board[a] == board[b] == board[c]:
      return board[a]
  if "" not in board:
    return "Draw"
  return None


@router.get("")
def get_game():
  return ttt_state


@router.post("/move")
def make_move(move: TTTMove):
  if ttt_state["winner"] is not None:
    return ttt_state
  idx = move.index
  if 0 <= idx < 9 and ttt_state["board"][idx] == "":
    ttt_state["board"][idx] = ttt_state["turn"]
    winner = check_winner(ttt_state["board"])
    if winner:
      ttt_state["winner"] = winner

      # 🎯 まるばつの結果をデータベースに保存
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO ttt_scores (winner) VALUES (?)", (winner,)
      )
      conn.commit()
      conn.close()

    else:
      ttt_state["turn"] = "O" if ttt_state["turn"] == "X" else "X"
  return ttt_state


@router.post("/reset")
def reset_game():
  ttt_state["board"] = [""] * 9
  ttt_state["turn"] = "X"
  ttt_state["winner"] = None
  return ttt_state