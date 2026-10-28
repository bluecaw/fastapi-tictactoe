from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.database import init_db
from app.routers import dnb, guess, rps, ttt


@asynccontextmanager
async def lifespan(app: FastAPI):
  # サーバー起動時にデータベースとテーブルを初期化
  init_db()
  yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各ゲームのルーター登録
app.include_router(ttt.router)
app.include_router(dnb.router)
app.include_router(rps.router)
app.include_router(guess.router)


@app.get("/", response_class=HTMLResponse)
def index():
  return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastAPI ミニゲームポータル</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin: 0; padding: 0; background: #f4f4f9; }
            header { background: #333; color: white; padding: 15px; display: flex; align-items: center; }
            .menu-btn { font-size: 24px; cursor: pointer; background: none; border: none; color: white; margin-right: 15px; }
            .sidebar { height: 100%; width: 0; position: fixed; z-index: 10; top: 0; left: 0; background-color: #111; overflow-x: hidden; transition: 0.3s; padding-top: 60px; text-align: left; }
            .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 18px; color: #818181; display: block; transition: 0.2s; }
            .sidebar a:hover { color: #f1f1f1; background: #222; }
            .sidebar .close-btn { position: absolute; top: 10px; right: 20px; font-size: 30px; }

            .content { padding: 20px; }
            .game-container { display: none; }
            .game-container.active { display: block; }

            .status { font-size: 18px; margin: 15px; font-weight: bold; color: #444; }
            button.reset-btn { padding: 8px 16px; font-size: 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 15px; }

            /* まるばつ */
            .ttt-board { display: grid; grid-template-columns: repeat(3, 90px); gap: 5px; justify-content: center; margin: 20px auto; }
            .ttt-cell { width: 90px; height: 90px; background: white; font-size: 36px; font-weight: bold; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px solid #ccc; border-radius: 8px; }

            /* ドット＆ボックス */
            .dnb-board { display: inline-block; margin: 20px auto; }
            .dnb-row { display: flex; align-items: center; justify-content: center; }
            .dot { width: 12px; height: 12px; background: #333; border-radius: 50%; }
            .h-line { width: 60px; height: 8px; background: #ddd; cursor: pointer; margin: 0 2px; border-radius: 4px; }
            .h-line.active { background: #007bff; }
            .v-line { width: 8px; height: 60px; background: #ddd; cursor: pointer; margin: 2px 0; border-radius: 4px; }
            .v-line.active { background: #007bff; }
            .box { width: 60px; height: 60px; background: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }

            /* じゃんけん */
            .rps-btns button { font-size: 24px; padding: 15px 25px; margin: 10px; cursor: pointer; border-radius: 10px; border: 2px solid #ccc; background: white; }
            .rps-btns button:hover { background: #e2e2e2; }

            /* 数字当て */
            .guess-box input { padding: 10px; font-size: 18px; width: 120px; text-align: center; }
            .guess-box button { padding: 10px 20px; font-size: 18px; background: #007bff; color: white; border: none; cursor: pointer; }
            .ranking-box { margin-top: 20px; background: white; padding: 10px; display: inline-block; border-radius: 8px; border: 1px solid #ddd; text-align: left; }
        </style>
    </head>
    <body>
        <div id="mySidebar" class="sidebar">
            <a href="javascript:void(0)" class="close-btn" onclick="closeNav()">&times;</a>
            <a href="javascript:void(0)" onclick="switchGame('ttt')">⭕❌ まるばつゲーム</a>
            <a href="javascript:void(0)" onclick="switchGame('dnb')">🔳 線引き陣取り</a>
            <a href="javascript:void(0)" onclick="switchGame('rps')">✌️ じゃんけん連勝バトル</a>
            <a href="javascript:void(0)" onclick="switchGame('guess')">🔢 数字当てゲーム</a>
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

            <!-- 2. ドット＆ボックス -->
            <div id="game-dnb" class="game-container">
                <div id="dnb-status" class="status">読み込み中...</div>
                <div id="dnb-board" class="dnb-board"></div>
                <button class="reset-btn" onclick="resetDnB()">リセット</button>
            </div>

            <!-- 3. じゃんけん連勝バトル -->
            <div id="game-rps" class="game-container">
                <div id="rps-status" class="status">読み込み中...</div>
                <div class="rps-btns">
                    <button onclick="playRPS('rock')">✊ グー</button>
                    <button onclick="playRPS('paper')">✋ パー</button>
                    <button onclick="playRPS('scissors')">✌️ チョキ</button>
                </div>
                <div id="rps-result" style="font-size: 20px; margin-top: 15px;"></div>
                <button class="reset-btn" onclick="resetRPS()">リセット</button>
            </div>

            <!-- 4. 数字当てゲーム -->
            <div id="game-guess" class="game-container">
                <div id="guess-status" class="status">読み込み中...</div>
                <div class="guess-box">
                    <input type="number" id="guess-input" min="1" max="100" placeholder="1〜100">
                    <button onclick="playGuess()">送信</button>
                </div>
                <br>
                <button class="reset-btn" onclick="resetGuess()">リセット</button>
                <div>
                    <div class="ranking-box">
                        <strong>🏆 クリアランキング (上位5件)</strong>
                        <ul id="ranking-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function openNav() { document.getElementById("mySidebar").style.width = "250px"; }
            function closeNav() { document.getElementById("mySidebar").style.width = "0"; }

            function switchGame(key) {
                closeNav();
                document.querySelectorAll('.game-container').forEach(el => el.classList.remove('active'));
                if (key === 'ttt') {
                    document.getElementById('game-ttt').classList.add('active');
                    document.getElementById('title').innerText = 'まるばつゲーム';
                    fetchTTT();
                } else if (key === 'dnb') {
                    document.getElementById('game-dnb').classList.add('active');
                    document.getElementById('title').innerText = '線引き陣取り';
                    fetchDnB();
                } else if (key === 'rps') {
                    document.getElementById('game-rps').classList.add('active');
                    document.getElementById('title').innerText = 'じゃんけん連勝バトル';
                    fetchRPS();
                } else if (key === 'guess') {
                    document.getElementById('game-guess').classList.add('active');
                    document.getElementById('title').innerText = '数字当てゲーム';
                    fetchGuess();
                }
            }

            // TTT
            async function fetchTTT() { renderTTT(await (await fetch('/api/ttt')).json()); }
            async function moveTTT(idx) { renderTTT(await (await fetch('/api/ttt/move', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:idx})})).json()); }
            async function resetTTT() { renderTTT(await (await fetch('/api/ttt/reset', {method:'POST'})).json()); }
            function renderTTT(data) {
                const b = document.getElementById('ttt-board'); b.innerHTML = '';
                data.board.forEach((val, idx) => {
                    const c = document.createElement('div'); c.className = 'ttt-cell'; c.innerText = val;
                    c.onclick = () => moveTTT(idx); b.appendChild(c);
                });
                document.getElementById('ttt-status').innerText = data.winner ? (data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`) : `現在の手番: ${data.turn}`;
            }

            // DnB
            async function fetchDnB() { renderDnB(await (await fetch('/api/dnb')).json()); }
            async function moveDnB(type, idx) { renderDnB(await (await fetch('/api/dnb/move', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:type, index:idx})})).json()); }
            async function resetDnB() { renderDnB(await (await fetch('/api/dnb/reset', {method:'POST'})).json()); }
            function renderDnB(data) {
                let html = '';
                html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[0]?'active':''}" onclick="moveDnB('h',0)"></div><div class="dot"></div><div class="h-line ${data.h_lines[1]?'active':''}" onclick="moveDnB('h',1)"></div><div class="dot"></div></div>`;
                html += `<div class="dnb-row"><div class="v-line ${data.v_lines[0]?'active':''}" onclick="moveDnB('v',0)"></div><div class="box">${data.boxes[0]}</div><div class="v-line ${data.v_lines[1]?'active':''}" onclick="moveDnB('v',1)"></div><div class="box">${data.boxes[1]}</div><div class="v-line ${data.v_lines[2]?'active':''}" onclick="moveDnB('v',2)"></div></div>`;
                html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[2]?'active':''}" onclick="moveDnB('h',2)"></div><div class="dot"></div><div class="h-line ${data.h_lines[3]?'active':''}" onclick="moveDnB('h',3)"></div><div class="dot"></div></div>`;
                html += `<div class="dnb-row"><div class="v-line ${data.v_lines[3]?'active':''}" onclick="moveDnB('v',3)"></div><div class="box">${data.boxes[2]}</div><div class="v-line ${data.v_lines[4]?'active':''}" onclick="moveDnB('v',4)"></div><div class="box">${data.boxes[3]}</div><div class="v-line ${data.v_lines[5]?'active':''}" onclick="moveDnB('v',5)"></div></div>`;
                html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[4]?'active':''}" onclick="moveDnB('h',4)"></div><div class="dot"></div><div class="h-line ${data.h_lines[5]?'active':''}" onclick="moveDnB('h',5)"></div><div class="dot"></div></div>`;
                document.getElementById('dnb-board').innerHTML = html;
                document.getElementById('dnb-status').innerText = data.winner ? (data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`) : `手番: ${data.turn} | P1: ${data.scores.P1}点 / P2: ${data.scores.P2}点`;
            }

            // RPS
            async function fetchRPS() { renderRPS(await (await fetch('/api/rps')).json()); }
            async function playRPS(hand) { renderRPS(await (await fetch('/api/rps/play', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({hand:hand})})).json()); }
            async function resetRPS() { renderRPS(await (await fetch('/api/rps/reset', {method:'POST'})).json()); }
            function renderRPS(data) {
                document.getElementById('rps-status').innerText = `現在の連勝数: ${data.streak} (最高: ${data.max_streak})`;
                let resText = '';
                if (data.result) {
                    const symbols = {'rock': '✊', 'paper': '✋', 'scissors': '✌️'};
                    resText = `あなた: ${symbols[data.last_user]} vs 相手: ${symbols[data.last_cpu]} → `;
                    if (data.result === 'Win') resText += 'あなたの勝ち！ 🎉';
                    else if (data.result === 'Lose') resText += 'あなたの負け... 😢';
                    else resText += 'あいこ！';
                }
                document.getElementById('rps-result').innerHTML = resText;
            }

            // Guess
            async function fetchGuess() { 
                const res = await (await fetch('/api/guess')).json();
                renderGuess(res);
                fetchRanking();
            }
            async function playGuess() {
                const val = parseInt(document.getElementById('guess-input').value);
                if (isNaN(val)) return;
                const res = await (await fetch('/api/guess/play', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({number:val})})).json();
                renderGuess(res);
                document.getElementById('guess-input').value = '';
                if (res.clear) { fetchRanking(); }
            }
            async function resetGuess() { 
                const res = await (await fetch('/api/guess/reset', {method:'POST'})).json();
                renderGuess(res);
            }
            function renderGuess(data) {
                document.getElementById('guess-status').innerHTML = `${data.message}<br><small>試行回数: ${data.attempts}回</small>`;
            }
            async function fetchRanking() {
                const res = await fetch('/api/guess/ranking');
                const ranking = await res.json();
                const listEl = document.getElementById('ranking-list');
                if (ranking.length === 0) {
                    listEl.innerHTML = '<li>まだクリア記録がありません</li>';
                    return;
                }
                let html = '';
                ranking.forEach((r, i) => {
                    html += `<li>第${i + 1}位: <strong>${r.attempts}回</strong> (${r.created_at})</li>`;
                });
                listEl.innerHTML = html;
            }

            fetchTTT();
        </script>
    </body>
    </html>
    """