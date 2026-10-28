import os
import json
from datetime import datetime, timezone, timedelta
import random
from fastapi import APIRouter
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel

if not firebase_admin._apps:
    firebase_key_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if firebase_key_json:
        cred = credentials.Certificate(json.loads(firebase_key_json))
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/api/guess", tags=["Number Guessing"])

guess_state = {
    "target": random.randint(1, 100),
    "attempts": 0,
    "message": "1から100までの数字を入力してね！",
    "clear": False,
}


class GuessMove(BaseModel):
    number: int


# 🇯🇵 日本時間 (JST = UTC+9) の定義
JST = timezone(timedelta(hours=9))

# （ゲームの状態や /play などの処理はそのまま）

@router.get("/ranking")
def get_guess_ranking():
    """Firestore から数字当てゲームのランキング（少ない試行回数順）を日本時間 (JST) に変換して取得"""
    try:
        # 少ない回数が上位なので ASCENDING (昇順)
        docs = (
            db.collection("guess_rankings")
            .order_by("attempts", direction=firestore.Query.ASCENDING)
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
                    "attempts": data.get("attempts"),
                    "created_at": created_at_str,
                }
            )
        return ranking
    except Exception as e:
        print(f"Error fetching guess ranking: {e}")
        return []


@router.get("")
def get_game():
    return {
        "message": guess_state["message"],
        "attempts": guess_state["attempts"],
        "clear": guess_state["clear"],
    }


@router.post("/play")
def play_guess(move: GuessMove):
    if guess_state["clear"]:
        return get_game()

    guess_state["attempts"] += 1
    val = move.number

    if val < guess_state["target"]:
        guess_state["message"] = f"{val} より大きいよ！ 📈"
    elif val > guess_state["target"]:
        guess_state["message"] = f"{val} より小さいよ！ 📉"
    else:
        guess_state["message"] = (
            f"🎉 正解！ 試行回数: {guess_state['attempts']}回"
        )
        guess_state["clear"] = True

        # 🎯 クリア時に Firestore にランキングを保存
        db.collection("guess_rankings").add(
            {
                "attempts": guess_state["attempts"],
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

    return get_game()


@router.post("/reset")
def reset_game():
    guess_state["target"] = random.randint(1, 100)
    guess_state["attempts"] = 0
    guess_state["message"] = "ゲームがリセットされました。1〜100を入力してね！"
    guess_state["clear"] = False
    return get_game()