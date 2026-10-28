import random
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


@router.get("/")
def get_game():
  return {
      "attempts": guess_state["attempts"],
      "message": guess_state["message"],
      "clear": guess_state["clear"],
  }


@router.post("/play")
def play_guess(move: GuessMove):
  if guess_state["clear"]:
    return {
        "attempts": guess_state["attempts"],
        "message": guess_state["message"],
        "clear": True,
    }

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

  return {
      "attempts": guess_state["attempts"],
      "message": guess_state["message"],
      "clear": guess_state["clear"],
  }


@router.post("/reset")
def reset_game():
  guess_state["target"] = random.randint(1, 100)
  guess_state["attempts"] = 0
  guess_state["message"] = "1から100までの数字を当て直してね！"
  guess_state["clear"] = False
  return {
      "attempts": 0,
      "message": guess_state["message"],
      "clear": False,
  }