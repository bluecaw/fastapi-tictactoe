import random
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/rps", tags=["Rock Paper Scissors"])

rps_state = {
    "streak": 0,
    "max_streak": 0,
    "last_user": None,
    "last_cpu": None,
    "result": None,
}


class RPSMove(BaseModel):
  hand: str


@router.get("/")
def get_game():
  return rps_state


@router.post("/play")
def play_rps(move: RPSMove):
  hands = ["rock", "paper", "scissors"]
  if move.hand not in hands:
    return rps_state

  cpu_hand = random.choice(hands)
  user_hand = move.hand

  rps_state["last_user"] = user_hand
  rps_state["last_cpu"] = cpu_hand

  if user_hand == cpu_hand:
    rps_state["result"] = "Draw"
  elif (
      (user_hand == "rock" and cpu_hand == "scissors")
      or (user_hand == "paper" and cpu_hand == "rock")
      or (user_hand == "scissors" and cpu_hand == "paper")
  ):
    rps_state["result"] = "Win"
    rps_state["streak"] += 1
    if rps_state["streak"] > rps_state["max_streak"]:
      rps_state["max_streak"] = rps_state["streak"]
  else:
    rps_state["result"] = "Lose"
    rps_state["streak"] = 0

  return rps_state


@router.post("/reset")
def reset_game():
  rps_state["streak"] = 0
  rps_state["last_user"] = None
  rps_state["last_cpu"] = None
  rps_state["result"] = None
  return rps_state