from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# どのオリジンからのアクセスも許可（ブラウザテスト用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ゲームの状態をシンプルにメモリ上で保持（簡易的）
game_state = {
    "board": [""] * 9,  # 9マスの状態 ("", "X", "O")
    "turn": "X",  # 手番
    "winner": None,  # 勝者 ("X", "O", "Draw", None)
}


class Move(BaseModel):
    index: int


def check_winner(board):
    # 勝利パターンの定義（縦・横・斜め）
    lines = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],  # 横
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],  # 縦
        [0, 4, 8],
        [2, 4, 6],  # 斜め
    ]
    for line in lines:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if "" not in board:
        return "Draw"
    return None


@app.get("/", response_class=HTMLResponse)
def index():
    # スマホやPCのブラウザからアクセスしたときに表示されるUI（フロントエンド一体型）
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastAPI まるばつゲーム</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #f4f4f9; }
            h1 { color: #333; }
            .board { display: grid; grid-template-columns: repeat(3, 100px); gap: 5px; justify-content: center; margin: 20px auto; }
            .cell { width: 100px; height: 100px; background: white; font-size: 40px; font-weight: bold; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px solid #ccc; border-radius: 8px; user-select: none; }
            .cell:hover { background: #f0f0f0; }
            #status { font-size: 20px; margin: 15px; font-weight: bold; color: #555; }
            button { padding: 10px 20px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>FastAPI まるばつゲーム</h1>
        <div id="status">読み込み中...</div>
        <div class="board" id="board"></div>
        <button onclick="resetGame()">リセット</button>

        <script>
            async function fetchState() {
                const res = await fetch('/game');
                const data = await res.json();
                render(data);
            }

            async function makeMove(index) {
                const res = await fetch('/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ index: index })
                });
                const data = await res.json();
                render(data);
            }

            async function resetGame() {
                const res = await fetch('/reset', { method: 'POST' });
                const data = await res.json();
                render(data);
            }

            function render(data) {
                const boardDiv = document.getElementById('board');
                boardDiv.innerHTML = '';
                data.board.forEach((val, idx) => {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.innerText = val;
                    cell.onclick = () => makeMove(idx);
                    boardDiv.appendChild(cell);
                });

                const statusDiv = document.getElementById('status');
                if (data.winner) {
                    if (data.winner === 'Draw') {
                        statusDiv.innerText = '引き分けです！';
                    } else {
                        statusDiv.innerText = `勝者: ${data.winner} 🎉`;
                    }
                } else {
                    statusDiv.innerText = `現在の手番: ${data.turn}`;
                }
            }

            fetchState();
        </script>
    </body>
    </html>
    """


@app.get("/game")
def get_game():
    return game_state


@app.post("/move")
def make_move(move: Move):
    if game_state["winner"] is not None:
        return game_state

    idx = move.index
    if 0 <= idx < 9 and game_state["board"][idx] == "":
        game_state["board"][idx] = game_state["turn"]
        winner = check_winner(game_state["board"])
        if winner:
            game_state["winner"] = winner
        else:
            game_state["turn"] = "O" if game_state["turn"] == "X" else "X"

    return game_state


@app.post("/reset")
def reset_game():
    game_state["board"] = [""] * 9
    game_state["turn"] = "X"
    game_state["winner"] = None
    return game_state