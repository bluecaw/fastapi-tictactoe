from datetime import datetime, timezone, timedelta
import random
from fastapi import APIRouter
from app.firebase import db
from firebase_admin import firestore
from pydantic import BaseModel

router = APIRouter(prefix="/api/slide", tags=["Slide Number"])
JST = timezone(timedelta(hours=9))

# 5x5盤面の状態 (1〜24、空欄は 0)
solved_board = list(range(1, 25)) + [0]

slide_state = {
    "board": list(solved_board),
    "is_playing": False,
    "moves": 0,
    "clear": False
}

class MoveRequest(BaseModel):
    index: int

def get_neighbors(idx):
    row, col = divmod(idx, 5)
    neighbors = []
    if row > 0: neighbors.append(idx - 5)
    if row < 4: neighbors.append(idx + 5)
    if col > 0: neighbors.append(idx - 1)
    if col < 4: neighbors.append(idx + 1)
    return neighbors

@router.get("")
def get_game():
    return slide_state

@router.post("/start")
def start_game():
    """ゲーム開始：完成形からランダムに動かして必ず解けるシャッフルを作成"""
    board = list(solved_board)
    # 100回ランダムな有効手を動かしてシャッフル
    for _ in range(100):
        zero_idx = board.index(0)
        neighbors = get_neighbors(zero_idx)
        target_idx = random.choice(neighbors)
        # スワップ
        board[zero_idx], board[target_idx] = board[target_idx], board[zero_idx]
    
    # 万が一シャッフル結果が偶然完成形になっていたらもう一度
    if board == solved_board:
        board[23], board[24] = board[24], board[23]

    slide_state["board"] = board
    slide_state["is_playing"] = True
    slide_state["moves"] = 0
    slide_state["clear"] = False
    return slide_state

@router.post("/move")
def make_move(req: MoveRequest):
    if not slide_state["is_playing"] or slide_state["clear"]:
        return slide_state

    idx = req.index
    board = slide_state["board"]
    zero_idx = board.index(0)

    # クリックしたパネルが空欄（0）の上下左右の隣接マスか判定
    if idx in get_neighbors(zero_idx):
        # スワップ
        board[zero_idx], board[idx] = board[idx], board[zero_idx]
        slide_state["moves"] += 1

        # クリア判定（1〜24が順番に並び、最後が0）
        if board == solved_board:
            slide_state["clear"] = True
            slide_state["is_playing"] = False

            # 🎯 Firestore にスコア（手数やクリア）を保存
            try:
                db.collection("slide_rankings").add({
                    "moves": slide_state["moves"],
                    "created_at": firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                print(f"Slide save error: {e}")

    return slide_state

@router.get("/ranking")
def get_ranking():
    """Firestore から少ない手数順のランキングを日本時間 (JST) で取得"""
    try:
        docs = (
            db.collection("slide_rankings")
            .order_by("moves", direction=firestore.Query.ASCENDING)
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
                created_at_str = created_at.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

            ranking.append({
                "moves": data.get("moves"),
                "created_at": created_at_str
            })
        return ranking
    except Exception as e:
        print(f"Error fetching slide ranking: {e}")
        return []