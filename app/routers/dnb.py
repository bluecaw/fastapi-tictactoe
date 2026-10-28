from app.database import get_db_connection
from fastapi import APIRouter
from pydantic import BaseModel

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
  """直近5件の対戦結果を取得"""
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT p1_score, p2_score, winner, created_at FROM dnb_scores ORDER BY id"
      " DESC LIMIT 5"
  )
  rows = cursor.fetchall()
  conn.close()
  return [
      {
          "p1_score": row["p1_score"],
          "p2_score": row["p2_score"],
          "winner": row["winner"],
          "created_at": row["created_at"],
      }
      for row in rows
  ]


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
  line_list = dnb_state["h_lines"] if move.type == "h" else dnb_state["v_lines"]
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

      # 🎯 ドット＆ボックスの結果をデータベースに保存
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO dnb_scores (p1_score, p2_score, winner) VALUES (?, ?,"
          " ?)",
          (
              dnb_state["scores"]["P1"],
              dnb_state["scores"]["P2"],
              dnb_state["winner"],
          ),
      )
      conn.commit()
      conn.close()

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