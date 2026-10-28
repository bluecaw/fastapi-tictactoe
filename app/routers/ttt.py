import os
import json
from datetime import datetime
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

router = APIRouter(prefix="/api/ttt", tags=["Tic-Tac-Toe"])

ttt_state = {
    "board": [""] * 9,
    "turn": "⭕",
    "winner": None,
}


class TTTMove(BaseModel):
    index: int


@router.get("/history")
def get_ttt_history():
    """Firestore から直近5件の履歴を取得"""
    try:
        docs = (
            db.collection("ttt_scores")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(5)
            .stream()
        )
        history = []
        for doc in docs:
            data = doc.to_dict()
            created_at = data.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at = str(datetime.now())

            history.append(
                {
                    "winner": data.get("winner"),
                    "created_at": created_at,
                }
            )
        return history
    except Exception:
        return []


@router.get("")
def get_game():
    return ttt_state


@router.post("/move")
def make_move(move: TTTMove):
    if ttt_state["winner"] is not None or ttt_state["board"][move.index] != "":
        return ttt_state

    ttt_state["board"][move.index] = ttt_state["turn"]

    # 勝利判定
    wins = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ]
    for w in wins:
        if (
            ttt_state["board"][w[0]]
            and ttt_state["board"][w[0]] == ttt_state["board"][w[1]]
            == ttt_state["board"][w[2]]
        ):
            ttt_state["winner"] = ttt_state["board"][w[0]]
            break

    if not ttt_state["winner"] and "" not in ttt_state["board"]:
        ttt_state["winner"] = "Draw"

    if ttt_state["winner"]:
        # 🎯 Firestore に履歴を保存
        db.collection("ttt_scores").add(
            {
                "winner": ttt_state["winner"],
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
    else:
        ttt_state["turn"] = "❌" if ttt_state["turn"] == "⭕" else "⭕"

    return ttt_state


@router.post("/reset")
def reset_game():
    ttt_state["board"] = [""] * 9
    ttt_state["turn"] = "⭕"
    ttt_state["winner"] = None
    return ttt_state