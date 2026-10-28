from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 1. まるばつゲーム (Tic-Tac-Toe) の状態 & ロジック
# --------------------------------------------------
ttt_state = {
    "board": [""] * 9,
    "turn": "X",
    "winner": None,
}

class TTTMove(BaseModel):
    index: int

def check_ttt_winner(board):
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for line in lines:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if "" not in board:
        return "Draw"
    return None

@app.get("/api/ttt")
def get_ttt():
    return ttt_state

@app.post("/api/ttt/move")
def move_ttt(move: TTTMove):
    if ttt_state["winner"] is not None:
        return ttt_state
    idx = move.index
    if 0 <= idx < 9 and ttt_state["board"][idx] == "":
        ttt_state["board"][idx] = ttt_state["turn"]
        winner = check_ttt_winner(ttt_state["board"])
        if winner:
            ttt_state["winner"] = winner
        else:
            ttt_state["turn"] = "O" if ttt_state["turn"] == "X" else "X"
    return ttt_state

@app.post("/api/ttt/reset")
def reset_ttt():
    ttt_state["board"] = [""] * 9
    ttt_state["turn"] = "X"
    ttt_state["winner"] = None
    return ttt_state

# --------------------------------------------------
# 2. ドットアンドボックス (Dot & Box 2x2) の状態 & ロジック
# --------------------------------------------------
# 2x2のマス（ドットは3x3）: 横線12本, 縦線12本のうちシンプル化のため 2x2のグリッド(横6本、縦6本)
# 水平線h: 3行x2列 (6本), 垂直線v: 2行x3列 (6本)
dnb_state = {
    "h_lines": [False] * 6, # 横線
    "v_lines": [False] * 6, # 縦線
    "boxes": [""] * 4,       # 4つのマス目の所有者 ("Player 1", "Player 2", "")
    "scores": {"P1": 0, "P2": 0},
    "turn": "P1",
    "winner": None
}

class DnBMove(BaseModel):
    type: str  # "h" or "v"
    index: int

def update_dnb_boxes():
    # 各マスが囲まれたかチェック
    # Box 0: h[0], h[2], v[0], v[1]
    # Box 1: h[1], h[3], v[1], v[2]
    # Box 2: h[2], h[4], v[3], v[4]
    # Box 3: h[3], h[5], v[4], v[5]
    box_requirements = [
        (0, 2, 0, 1),
        (1, 3, 1, 2),
        (2, 4, 3, 4),
        (3, 5, 4, 5),
    ]
    made_box = False
    for i, (h1, h2, v1, v2) in enumerate(box_requirements):
        if dnb_state["boxes"][i] == "":
            if dnb_state["h_lines"][h1] and dnb_state["h_lines"][h2] and dnb_state["v_lines"][v1] and dnb_state["v_lines"][v2]:
                dnb_state["boxes"][i] = dnb_state["turn"]
                dnb_state["scores"][dnb_state["turn"]] += 1
                made_box = True
    return made_box

@app.get("/api/dnb")
def get_dnb():
    return dnb_state

@app.post("/api/dnb/move")
def move_dnb(move: DnBMove):
    if dnb_state["winner"] is not None:
        return dnb_state
    
    line_list = dnb_state["h_lines"] if move.type == "h" else dnb_state["v_lines"]
    if 0 <= move.index < 6 and not line_list[move.index]:
        line_list[move.index] = True
        scored = update_dnb_boxes()
        
        # 全ての箱が埋まったら終了
        if "" not in dnb_state["boxes"]:
            if dnb_state["scores"]["P1"] > dnb_state["scores"]["P2"]:
                dnb_state["winner"] = "P1"
            elif dnb_state["scores"]["P2"] > dnb_state["scores"]["P1"]:
                dnb_state["winner"] = "P2"
            else:
                dnb_state["winner"] = "Draw"
        elif not scored:
            # マスを獲得できなかった場合のみ交代
            dnb_state["turn"] = "P2" if dnb_state["turn"] == "P1" else "P1"

    return dnb_state

@app.post("/api/dnb/reset")
def reset_dnb():
    dnb_state["h_lines"] = [False] * 6
    dnb_state["v_lines"] = [False] * 6
    dnb_state["boxes"] = [""] * 4
    dnb_state["scores"] = {"P1": 0, "P2": 0}
    dnb_state["turn"] = "P1"
    dnb_state["winner"] = None
    return dnb_state

# --------------------------------------------------
# 3. フロントエンド (HTML / CSS / JS)
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastAPI ミニゲーム集</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin: 0; padding: 0; background: #f4f4f9; }
            
            /* ヘッダーとサイドバー */
            header { background: #333; color: white; padding: 15px; display: flex; align-items: center; }
            .menu-btn { font-size: 24px; cursor: pointer; background: none; border: none; color: white; margin-right: 15px; }
            .sidebar { height: 100%; width: 0; position: fixed; z-index: 10; top: 0; left: 0; background-color: #111; overflow-x: hidden; transition: 0.3s; padding-top: 60px; text-align: left; }
            .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 18px; color: #818181; display: block; transition: 0.2s; }
            .sidebar a:hover { color: #f1f1f1; background: #222; }
            .sidebar .close-btn { position: absolute; top: 10px; right: 20px; font-size: 30px; }

            .content { padding: 20px; }
            .game-container { display: none; }
            .game-container.active { display: block; }

            /* まるばつゲーム用 */
            .ttt-board { display: grid; grid-template-columns: repeat(3, 90px); gap: 5px; justify-content: center; margin: 20px auto; }
            .ttt-cell { width: 90px; height: 90px; background: white; font-size: 36px; font-weight: bold; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px solid #ccc; border-radius: 8px; }

            /* ドットアンドボックス用 */
            .dnb-board { display: inline-block; margin: 20px auto; }
            .dnb-row { display: flex; align-items: center; justify-content: center; }
            .dot { width: 12px; height: 12px; background: #333; border-radius: 50%; }
            .h-line { width: 60px; height: 8px; background: #ddd; cursor: pointer; margin: 0 2px; border-radius: 4px; }
            .h-line.active { background: #007bff; }
            .v-line { width: 8px; height: 60px; background: #ddd; cursor: pointer; margin: 2px 0; border-radius: 4px; }
            .v-line.active { background: #007bff; }
            .box { width: 60px; height: 60px; background: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }

            .status { font-size: 18px; margin: 15px; font-weight: bold; color: #444; }
            button.reset-btn { padding: 8px 16px; font-size: 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="mySidebar" class="sidebar">
            <a href="javascript:void(0)" class="close-btn" onclick="closeNav()">&times;</a>
            <a href="javascript:void(0)" onclick="switchGame('ttt')">⭕❌ まるばつゲーム</a>
            <a href="javascript:void(0)" onclick="switchGame('dnb')">🔳 線引き陣取り (Dot & Box)</a>
        </div>

        <header>
            <button class="menu-btn" onclick="openNav()">&#9776;</button>
            <h2 id="title" style="margin:0;">まるばつゲーム</h2>
        </header>

        <div class="content">
            <!-- 1. まるばつゲーム -->
            <div id="game-ttt" class="game-container active">
                <div id="ttt-status" class="status">読み込み中...</div>
                <div class="ttt-board" id="ttt-board"></div>
                <button class="reset-btn" onclick="resetTTT()">リセット</button>
            </div>

            <!-- 2. ドットアンドボックス -->
            <div id="game-dnb" class="game-container">
                <div id="dnb-status" class="status">読み込み中...</div>
                <div id="dnb-board" class="dnb-board"></div>
                <button class="reset-btn" onclick="resetDnB()">リセット</button>
            </div>
        </div>

        <script>
            // サイドバー制御
            function openNav() { document.getElementById("mySidebar").style.width = "250px"; }
            function closeNav() { document.getElementById("mySidebar").style.width = "0"; }

            function switchGame(gameKey) {
                closeNav();
                document.querySelectorAll('.game-container').forEach(el => el.classList.remove('active'));
                if (gameKey === 'ttt') {
                    document.getElementById('game-ttt').classList.add('active');
                    document.getElementById('title').innerText = 'まるばつゲーム';
                    fetchTTT();
                } else {
                    document.getElementById('game-dnb').classList.add('active');
                    document.getElementById('title').innerText = '線引き陣取り (Dot & Box)';
                    fetchDnB();
                }
            }

            // --- まるばつゲーム用 JS ---
            async function fetchTTT() {
                const res = await fetch('/api/ttt');
                const data = await res.json();
                renderTTT(data);
            }
            async function moveTTT(idx) {
                const res = await fetch('/api/ttt/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ index: idx })
                });
                renderTTT(await res.json());
            }
            async function resetTTT() {
                const res = await fetch('/api/ttt/reset', { method: 'POST' });
                renderTTT(await res.json());
            }
            function renderTTT(data) {
                const boardDiv = document.getElementById('ttt-board');
                boardDiv.innerHTML = '';
                data.board.forEach((val, idx) => {
                    const cell = document.createElement('div');
                    cell.className = 'ttt-cell';
                    cell.innerText = val;
                    cell.onclick = () => moveTTT(idx);
                    boardDiv.appendChild(cell);
                });
                const statusDiv = document.getElementById('ttt-status');
                if (data.winner) {
                    statusDiv.innerText = data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`;
                } else {
                    statusDiv.innerText = `現在の手番: ${data.turn}`;
                }
            }

            // --- ドットアンドボックス用 JS ---
            async function fetchDnB() {
                const res = await fetch('/api/dnb');
                renderDnB(await res.json());
            }
            async function moveDnB(type, idx) {
                const res = await fetch('/api/dnb/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ type: type, index: idx })
                });
                renderDnB(await res.json());
            }
            async function resetDnB() {
                const res = await fetch('/api/dnb/reset', { method: 'POST' });
                renderDnB(await res.json());
            }
            function renderDnB(data) {
                const boardDiv = document.getElementById('dnb-board');
                boardDiv.innerHTML = '';
                
                // 2x2のドットアンドボックス描画
                // 行0: H0, H1 / 行1: V0 B0 V1 B1 V2 / 行2: H2, H3 / 行3: V3 B2 V4 B3 V5 / 行4: H4, H5
                let html = '';
                
                // 行0 (点-横線-点-横線-点)
                html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[0]?'active':''}" onclick="moveDnB('h',0)"></div><div class="dot"></div><div class="h-line ${data.h_lines[1]?'active':''}" onclick="moveDnB('h',1)"></div><div class="dot"></div></div>`;
                // 行1 (縦線-マス-縦線-マス-縦線)
                html += `<div class="dnb-row"><div class="v-line ${data.v_lines[0]?'active':''}" onclick="moveDnB('v',0)"></div><div class="box">${data.boxes[0]}</div><div class="v-line ${data.v_lines[1]?'active':''}" onclick="moveDnB('v',1)"></div><div class="box">${data.boxes[1]}</div><div class="v-line ${data.v_lines[2]?'active':''}" onclick="moveDnB('v',2)"></div></div>`;
                // 行2
                html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[2]?'active':''}" onclick="moveDnB('h',2)"></div><div class="dot"></div><div class="h-line ${data.h_lines[3]?'active':''}" onclick="moveDnB('h',3)"></div><div class="dot"></div></div>`;
                // 行3
                html += `<div class="dnb-row"><div class="v-line ${data.v_lines[3]?'active':''}" onclick="moveDnB('v',3)"></div><div class="box">${data.boxes[2]}</div><div class="v-line ${data.v_lines[4]?'active':''}" onclick="moveDnB('v',4)"></div><div class="box">${data.boxes[3]}</div><div class="v-line ${data.v_lines[5]?'active':''}" onclick="moveDnB('v',5)"></div></div>`;
                // 行4
                html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[4]?'active':''}" onclick="moveDnB('h',4)"></div><div class="dot"></div><div class="h-line ${data.h_lines[5]?'active':''}" onclick="moveDnB('h',5)"></div><div class="dot"></div></div>`;
                
                boardDiv.innerHTML = html;

                const statusDiv = document.getElementById('dnb-status');
                if (data.winner) {
                    statusDiv.innerText = data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`;
                } else {
                    statusDiv.innerText = `現在の手番: ${data.turn} | P1: ${data.scores.P1}点 / P2: ${data.scores.P2}点`;
                }
            }

            fetchTTT();
        </script>
    </body>
    </html>
    """