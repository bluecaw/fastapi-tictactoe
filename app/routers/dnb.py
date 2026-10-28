import os
import json
from datetime import datetime
from fastapi import APIRouter
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel

# --- Firebase の初期化（重複初期化防止） ---
if not firebase_admin._apps:
    # Renderの環境変数から秘密鍵のJSON文字列を取得して辞書に変換
    firebase_key_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if firebase_key_json:
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # ローカル開発用（ファイルを直接読む）
        cred = credentials.Certificate("serviceAccountKey.json")
    
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/api/dnb", tags=["Dot and Box"])

dnb_state = {
    "h_lines": [False] * 6,
    "v_lines": [False] * 6,
    "boxes": [""] * 4,
    "scores": {"P1": 0, "P2": 0},
    "turn": "P1",
    "winner": None,
}


class DnBMove(BaseModel):
    type: str
    index: int


@router.get("/history")
def get_dnb_history():
    """Firestore から直近5件の対戦結果を取得"""
    try:
        # created_at の降順で最大5件取得
        docs = (
            db.collection("dnb_scores")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(5)
            .stream()
        )

        history = []
        for doc in docs:
            data = doc.to_dict()
            # タイムスタンプを文字列に変換
            created_at = data.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at = str(datetime.now())

            history.append(
                {
                    "p1_score": data.get("p1_score"),
                    "p2_score": data.get("p2_score"),
                    "winner": data.get("winner"),
                    "created_at": created_at,
                }
            )
        return history
    except Exception as e:
        # テーブル（コレクション）がまだ無い場合などのエラー対策
        return []


def update_boxes():
    box_reqs = [(0, 2, 0, 1), (1, 3, 1, 2), (2, 4, 3, 4), (3, 5, 4, 5)]
    scored = False
    for i, (h1, h2, v1, v2) in enumerate(box_reqs):
        if dnb_state["boxes"][i] == "":
            if (
                dnb_state["h_lines"][h1]
                and dnb_state["h_lines"][h2]
                and dnb_state["v_lines"][v1]
                and dnb_state["v_lines"][v2]
            ):
                dnb_state["boxes"][i] = dnb_state["turn"]
                dnb_state["scores"][dnb_state["turn"]] += 1
                scored = True
    return scored


@router.get("")
def get_game():
    return dnb_state


@router.post("/move")
def make_move(move: DnBMove):
    if dnb_state["winner"] is not None:
        return dnb_state
    line_list = (
        dnb_state["h_lines"] if move.type == "h" else dnb_state["v_lines"]
    )
    if 0 <= move.index < len(line_list) and not line_list[move.index]:
        line_list[move.index] = True
        scored = update_boxes()
        if "" not in dnb_state["boxes"]:
            if dnb_state["scores"]["P1"] > dnb_state["scores"]["P2"]:
                dnb_state["winner"] = "P1"
            elif dnb_state["scores"]["P2"] > dnb_state["scores"]["P1"]:
                dnb_state["winner"] = "P2"
            else:
                dnb_state["winner"] = "Draw"

            # 🎯 Firestore にゲーム結果を保存
            db.collection("dnb_scores").add(
                {
                    "p1_score": dnb_state["scores"]["P1"],
                    "p2_score": dnb_state["scores"]["P2"],
                    "winner": dnb_state["winner"],
                    "created_at": firestore.SERVER_TIMESTAMP,
                }
            )

        elif not scored:
            dnb_state["turn"] = "P2" if dnb_state["turn"] == "P1" else "P1"
    return dnb_state


@router.post("/reset")
def reset_game():
    dnb_state["h_lines"] = [False] * 6
    dnb_state["v_lines"] = [False] * 6
    dnb_state["boxes"] = [""] * 4
    dnb_state["scores"] = {"P1": 0, "P2": 0}
    dnb_state["turn"] = "P1"
    dnb_state["winner"] = None
    return dnb_state