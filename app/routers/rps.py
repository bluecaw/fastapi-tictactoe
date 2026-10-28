from datetime import datetime
import random
from fastapi import APIRouter
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/api/rps", tags=["Rock-Paper-Scissors"])

rps_state = {
    "streak": 0,
    "max_streak": 0,
    "last_user": None,
    "last_cpu": None,
    "result": None,
}


class RPSPlay(BaseModel):
    hand: str


@router.get("/ranking")
def get_rps_ranking():
    """Firestore から上位5件の連勝ランキングを取得"""
    try:
        docs = (
            db.collection("rps_rankings")
            .order_by("streak", direction=firestore.Query.DESCENDING)
            .limit(5)
            .stream()
        )
        ranking = []
        for doc in docs:
            data = doc.to_dict()
            created_at = data.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at = str(datetime.now())

            ranking.append(
                {
                    "streak": data.get("streak"),
                    "created_at": created_at,
                }
            )
        return ranking
    except Exception:
        return []


@router.get("")
def get_game():
    return rps_state


@router.post("/play")
def play_rps(play: RPSPlay):
    hands = ["rock", "paper", "scissors"]
    cpu_hand = random.choice(hands)
    user_hand = play.hand

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
        if rps_state["streak"] > 0:
            # 🎯 負けた時点でランキング（連勝記録）を Firestore に保存
            db.collection("rps_rankings").add(
                {
                    "streak": rps_state["streak"],
                    "created_at": firestore.SERVER_TIMESTAMP,
                }
            )
        rps_state["streak"] = 0

    return rps_state


@router.post("/reset")
def reset_game():
    rps_state["streak"] = 0
    rps_state["last_user"] = None
    rps_state["last_cpu"] = None
    rps_state["result"] = None
    return rps_state