from datetime import datetime, timezone, timedelta
import json
import os
import random
from fastapi import APIRouter
from app.firebase import db  # 共通モジュールを使っている場合
from firebase_admin import firestore
from pydantic import BaseModel

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


# 🇯🇵 日本時間 (JST = UTC+9) の定義
JST = timezone(timedelta(hours=9))

# （ゲームの状態や /play などの処理はそのまま）

@router.get("/ranking")
def get_rps_ranking():
    """Firestore からストレーク（連勝）ランキングを日本時間 (JST) に変換して取得"""
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
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                created_at_jst = created_at.astimezone(JST)
                created_at_str = created_at_jst.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

            ranking.append(
                {
                    "streak": data.get("streak"),
                    "created_at": created_at_str,
                }
            )
        return ranking
    except Exception as e:
        print(f"Error fetching rps ranking: {e}")
        return []


@router.get("")
def get_game():
    return rps_state


@router.post("/play")
def play_rps(play: RPSPlay):
    try:
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
                # Firestore への保存でエラーが起きてもアプリを落とさないようにする
                try:
                    db.collection("rps_rankings").add(
                        {
                            "streak": rps_state["streak"],
                            "created_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                except Exception as db_err:
                    print(f"Firestore save error: {db_err}")
            rps_state["streak"] = 0

        return rps_state
    except Exception as e:
        print(f"Error in play_rps: {e}")
        return {"error": str(e)}


@router.post("/reset")
def reset_game():
    rps_state["streak"] = 0
    rps_state["last_user"] = None
    rps_state["last_cpu"] = None
    rps_state["result"] = None
    return rps_state