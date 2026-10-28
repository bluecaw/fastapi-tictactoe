from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/ttt", tags=["Tic-Tac-Toe"])

ttt_state = {"board": [""] * 9, "turn": "X", "winner": None}


class TTTMove(BaseModel):
  index: int


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


@router.get("/")
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
    else:
      ttt_state["turn"] = "O" if ttt_state["turn"] == "X" else "X"
  return ttt_state


@router.post("/reset")
def reset_game():
  ttt_state["board"] = [""] * 9
  ttt_state["turn"] = "X"
  ttt_state["winner"] = None
  return ttt_state