# -*- coding: utf-8 -*-
"""英単語トレーニング 統合版
人選択画面（title）→ コース選択（Junior/High）→ ゲーム画面（game）
"""

import streamlit as st
import csv
import json
import os
import random
import time
import base64
import re

# レベルアップ条件
STREAK_TO_LEVEL_UP = 5

# コース定義（C対応：中学生／高校生でフォルダとハイスコアを分ける）
COURSES = ["Junior", "High"]
COURSE_LABELS = {"Junior": "中学生", "High": "高校生"}
COURSE_ICONS = {"Junior": "🎒", "High": "📗"}

# ---------------------------------------------------------
# セッション初期化
# ---------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "select"   # 最初は人選択画面

if "player" not in st.session_state:
    st.session_state.player = None

# ---------------------------------------------------------
# プレイヤーデータ
# ---------------------------------------------------------
players = [
    {"name": "ゆそ", "color": "#6ed46e", "icon": "🐶"},
    {"name": "しん", "color": "#6eb6ff", "icon": "🍏"},
    {"name": "キャス", "color": "#c49b6e", "icon": "🐱"},
    {"name": "ファザ", "color": "#ff9ad6", "icon": "🧢"},
    {"name": "ゲスト", "color": "#b28bff", "icon": "❔"},
]

# ---------------------------------------------------------
# 背景CSS（豪華版＋スマホ縦画面対応）
# ---------------------------------------------------------
background_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;900&display=swap');

html, body, [class*="css"], .stMarkdown, .stButton>button, p, span, div {
    font-family: 'M PLUS Rounded 1c', 'Hiragino Maru Gothic ProN', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #89cff0, #f6d5f7, #ffe3f3, #cdeaff);
    background-size: 300% 300%;
    animation: bgmove 12s ease infinite;
}
@keyframes bgmove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ---- 画面全体の余白を詰める（老眼対策：1画面に収める） ---- */
.block-container {
    padding-top: 2.8rem !important;
    padding-bottom: 0.8rem !important;
    padding-left: 0.9rem !important;
    padding-right: 0.9rem !important;
}
div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    gap: 0.2rem !important;
}
.stButton {
    margin-bottom: 2px !important;
}
div[data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.2rem;
}

/* ---- ボタン全体を可愛く ---- */
.stButton>button {
    border: none;
    border-radius: 18px;
    padding: 0.6em 1.2em;
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #6ed4a0, #4fb3ff);
    box-shadow: 0 4px 0 rgba(0,0,0,0.15), 0 6px 14px rgba(0,0,0,0.12);
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    width: 100%;
}
.stButton>button:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 6px 0 rgba(0,0,0,0.18), 0 10px 18px rgba(0,0,0,0.15);
    color: #fff;
}
.stButton>button:active {
    transform: translateY(2px);
    box-shadow: 0 1px 0 rgba(0,0,0,0.15);
}

/* ---- 4択の選択肢ボタン：遠くからでも見やすいように文字を大きく、余白は小さめに ---- */
/* ★1.5倍対応→さらに1.5倍：40px→60px→90px */
div[class*="st-key-choice_btn_"] .stButton>button {
    font-size: 90px;
    padding: 0.35em 0.4em;
    line-height: 1.2;
}

/* ---- プレイヤー選択カード ---- */
.pixel-card {
    padding: 14px;
    border-radius: 18px;
    border: 3px solid #fff;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.18), 0px 0px 12px rgba(255,255,255,0.6) inset;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    margin: 6px 0 14px 0;
    transition: transform 0.2s;
}
.pixel-card:hover {
    transform: scale(1.05);
    box-shadow: 0px 8px 24px rgba(0,0,0,0.24);
}

.name-title {
    font-size: 40px;
    font-weight: 900;
    color: #fff;
    text-align: center;
    text-shadow: 3px 3px 0px rgba(0,0,0,0.25);
    animation: float 2s infinite ease-in-out;
    margin-bottom: 4px;
}
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
    100% { transform: translateY(0px); }
}

.tap-guide {
    font-size: 18px;
    text-align: center;
    color: #fff;
    text-shadow: 2px 2px 0px rgba(0,0,0,0.2);
    animation: blink 1.5s infinite;
}
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0.4; }
    100% { opacity: 1; }
}

.icon {
    font-size: 34px;
    margin-bottom: 6px;
}

/* ---- 出題カード ---- */
.question-card {
    background: rgba(255,255,255,0.92);
    border-radius: 18px;
    padding: 18px 14px;
    margin: 8px 0 12px 0;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    text-align: center;
}
.question-card .en {
    font-size: 38px;
    font-weight: 900;
    color: #2b6cb0;
    letter-spacing: 1px;
}
.question-card .example {
    font-size: 16px;
    color: #555;
    margin-top: 8px;
}

/* ---- レベル表示バッジ ---- */
.level-badge {
    display: inline-block;
    background: linear-gradient(135deg, #ffd166, #ff9a3c);
    color: #fff;
    padding: 5px 16px;
    border-radius: 999px;
    font-weight: 900;
    font-size: 18px;
    box-shadow: 0 3px 0 rgba(0,0,0,0.15);
}

.wordbook-badge {
    display: inline-block;
    background: rgba(255,255,255,0.85);
    color: #444;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 700;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.course-badge {
    display: inline-block;
    background: rgba(255,255,255,0.85);
    color: #2b6cb0;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 15px;
    font-weight: 900;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.score-panel {
    background: rgba(255,255,255,0.85);
    border-radius: 14px;
    padding: 10px 16px;
    margin-top: 8px;
    font-size: 18px;
    font-weight: 700;
    color: #333;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* ---- スマホ縦画面：さらに文字大き目・枠小さめに ---- */
@media (max-width: 480px) {
    .block-container {
        padding-top: 2.0rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    .name-title { font-size: 30px; margin-bottom: 2px; }
    .tap-guide { font-size: 16px; }
    .pixel-card { padding: 8px; margin: 4px 0 8px 0; font-size: 17px; }
    .icon { font-size: 26px; margin-bottom: 2px; }
    .question-card { padding: 12px 8px; margin: 6px 0 8px 0; }
    .question-card .en { font-size: 30px; }
    .question-card .example { font-size: 14px; margin-top: 4px; }
    .stButton>button { padding: 0.55em 0.8em; font-size: 22px; }
    div[class*="st-key-choice_btn_"] .stButton>button { font-size: 77px; padding: 0.3em 0.35em; }
    .score-panel { padding: 7px 10px; font-size: 15px; margin-top: 4px; }
    .level-badge { font-size: 15px; padding: 4px 12px; }
    .wordbook-badge, .course-badge { font-size: 12px; padding: 3px 10px; }
}
</style>
"""
st.markdown(background_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# game.py の本体ロジック
# ---------------------------------------------------------
import requests
import streamlit.components.v1 as components

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORD_DIR = os.path.join(BASE_DIR, "Word_Data")
PERSONAL_DIR = os.path.join(BASE_DIR, "Personal_Data")
MUSIC_DIR = os.path.join(BASE_DIR, "MUSIC")
os.makedirs(WORD_DIR, exist_ok=True)
os.makedirs(PERSONAL_DIR, exist_ok=True)
for _c in COURSES:
    os.makedirs(os.path.join(WORD_DIR, _c), exist_ok=True)

# D対応：効果音ファイル
SOUND_CORRECT_PATH = os.path.join(MUSIC_DIR, "正解ping.mp3")
SOUND_WRONG_PATH = os.path.join(MUSIC_DIR, "不正解boo.mp3")


def ensure_audio_unlock():
    """スマホ（iOS/Android）の自動再生制限を回避するための仕込み。

    モバイルブラウザは「ユーザーの直接操作（タップ等）の中で再生された
    音」しか自動再生を許可しないことが多い。Streamlitはボタン操作→
    サーバー処理→再描画、という非同期の流れになるため、Python側から
    後追いで <audio autoplay> を差し込んでも、モバイルでは再生がブロック
    されてしまう。

    対策として、
      1) 親ページに一つだけ <audio> 要素を用意しておき、
      2) ページ内の最初のタップ/クリックのタイミングで一度だけ
         その要素を鳴らして（すぐ一時停止）「このタブでは音声再生が
         許可された」状態を作っておく
      3) 以降は play_sound() で同じ要素の src を差し替えて鳴らす
    という「オーディオのアンロック」パターンを使う。
    ページ内のどこかを一度タップすればそれ以降の効果音は鳴るようになる。
    """
    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            if (doc.__claudeAppAudioUnlockSetup) { return; }
            doc.__claudeAppAudioUnlockSetup = true;

            let player = doc.getElementById('claude-app-audio-player');
            if (!player) {
                player = doc.createElement('audio');
                player.id = 'claude-app-audio-player';
                player.style.display = 'none';
                doc.body.appendChild(player);
            }
            doc.__claudeAppAudioPlayer = player;

            function unlock() {
                player.play().then(function () {
                    player.pause();
                }).catch(function () {});
                doc.removeEventListener('touchstart', unlock, true);
                doc.removeEventListener('click', unlock, true);
            }
            doc.addEventListener('touchstart', unlock, true);
            doc.addEventListener('click', unlock, true);
        })();
        </script>
        """,
        height=0,
    )


def play_sound(path):
    """mp3をbase64埋め込みで再生する（スマホの自動再生制限対策版）

    ★修正点：
    以前は毎回新しい <audio autoplay> をiframeごと生成する方式だったが、
    PC（Chrome等）では動いてもスマホ（iOS/Android）では非同期に挿入された
    audioタグの自動再生がブロックされ、音が鳴らないことがあった。
    ensure_audio_unlock() で用意した「アンロック済みの永続<audio>要素」の
    src を毎回差し替えて再生する方式にすることで、一度ユーザーが画面を
    タップした後であれば、スマホでも確実に鳴るようにしている。
    """
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        components.html(
            f"""
            <script>
            (function () {{
                const doc = window.parent.document;
                let player = doc.getElementById('claude-app-audio-player');
                if (!player) {{
                    player = doc.createElement('audio');
                    player.id = 'claude-app-audio-player';
                    player.style.display = 'none';
                    doc.body.appendChild(player);
                }}
                player.src = "data:audio/mp3;base64,{b64}";
                player.currentTime = 0;
                player.play().catch(function () {{}});
            }})();
            </script>
            <!-- nonce:{time.time()} -->
            """,
            height=0,
        )
    except Exception:
        pass


def get_word_dir(course=None):
    course = course or st.session_state.get("course") or COURSES[0]
    return os.path.join(WORD_DIR, course)


def current_player_name():
    """今選ばれているプレイヤー名を返す（ファイル名に使う）"""
    p = st.session_state.get("player")
    name = p["name"] if isinstance(p, dict) else p
    return name or "guest"


def missed_file_path(player_name=None, course=None):
    player_name = player_name or current_player_name()
    course = course or st.session_state.get("course") or COURSES[0]
    return os.path.join(PERSONAL_DIR, f"missed_words_{player_name}_{course}.json")


def ranking_file_path(course=None, mode_suffix=""):
    course = course or st.session_state.get("course") or COURSES[0]
    return os.path.join(PERSONAL_DIR, f"ranking_{course}{mode_suffix}.json")


# Firebase（任意・記録の永続化に必須）
# ★2対応：Streamlit Community Cloud はアプリが再起動（スリープ復帰・再デプロイ等）すると
#   コンテナがgitの状態にリセットされ、実行中にローカルへ書き込んだ
#   Personal_Data/*.json は消えてしまう（＝ローカルファイル保存だけでは記録は残せない）。
#   これを防ぐには、Firebase Realtime Database等の外部ストレージに保存する必要がある。
#   URLはソースコードに直書きせず、Streamlit Cloudの「Settings > Secrets」に
#   FIREBASE_DB_URL = "https://xxxx-default-rtdb.firebaseio.com"
#   の形で設定する（.streamlit/secrets.toml をローカルで使う場合も同様のキー名）。
try:
    FIREBASE_DB_URL = st.secrets.get("FIREBASE_DB_URL", "")
except Exception:
    FIREBASE_DB_URL = ""
# ▼ Secretsに末尾スラッシュ付きで貼られていても二重スラッシュにならないようにする
FIREBASE_DB_URL = FIREBASE_DB_URL.rstrip("/")

if "css_loaded" not in st.session_state:
    st.markdown("""
    <style>
    @keyframes flash {
        0% { background-color: yellow; }
        100% { background-color: transparent; }
    }
    @keyframes shake {
        0% { transform: translate(0px, 0px); }
        25% { transform: translate(-5px, 0px); }
        50% { transform: translate(5px, 0px); }
        75% { transform: translate(-5px, 0px); }
        100% { transform: translate(0px, 0px); }
    }
    </style>
    """, unsafe_allow_html=True)
    st.session_state.css_loaded = True

# ▼ スマホでの効果音再生対策：アンロック用リスナーを仕込む（毎回呼んでも冪等）
ensure_audio_unlock()


def show_effect(effect_type, review_times):

    if effect_type == "correct":

        if review_times > 0:
            html = f"""
            <div style="padding:10px; animation: flash 0.5s;">
                <h2 style="color:#00cc44;">✨ ピンポン！ 正解！ ✨</h2>
                <h3 style="color:#006600;">復習回数：{review_times}/5</h3>
            </div>
            """
        else :
            html = f"""
            <div style="padding:10px; animation: flash 0.5s;">
                <h2 style="color:#00cc44;">✨ ピンポン！ 正解！ ✨</h2>
            </div>
            """
        return html

    elif effect_type == "wrong":
        return """
        <div style="padding:10px; animation: shake 0.3s;">
            <h2 style="color:#ff3333;">💥 ブブー！ 不正解！ 💥</h2>
        </div>
        """

    elif effect_type == "levelup":
        return """
        <div style="padding:10px; animation: flash 1s;">
            <h2 style="color:#ffaa00;">🎉 レベルアップ！ 🎉</h2>
        </div>
        """

    return ""

# -------------------------
# 単語データ構造（Pyxel版を移植）
# -------------------------
class WordBasic:
    def __init__(self, english, japanese, example_en=None, example_ja=None, note=None):
        self.english = english
        self.japanese = japanese
        self.example_en = example_en
        self.example_ja = example_ja
        self.note = note

    def prompt(self):
        return f"英単語: {self.english}"

    def correct_choice(self):
        return self.japanese


class WordQuiz:
    def __init__(self, question, choices, answer, japanese):
        self.question = question
        self.choices = list(choices)
        self.answer = answer
        self.japanese = japanese

    def prompt(self):
        return self.question

    def correct_choice(self):
        return self.answer


# -------------------------
# CSV読み込み（Pyxel版を移植）
# -------------------------
def load_words(filename):
    words = []
    if not filename or not os.path.exists(filename):
        return words

    with open(filename, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            row = [c.strip() for c in row]
            while row and row[-1] == "":
                row.pop()

            n = len(row)
            if n == 7:
                q, c1, c2, c3, c4, ans, jp = row
                words.append(WordQuiz(q, [c1, c2, c3, c4], ans, jp))
            elif n == 2:
                words.append(WordBasic(row[0], row[1]))
            elif n == 3:
                words.append(WordBasic(row[0], row[1], note=row[2]))
            elif n == 4:
                words.append(WordBasic(row[0], row[1], row[2], row[3]))
    return words


# -------------------------
# 間違えた単語の保存（プレイヤー×コースごと）
# -------------------------
def load_missed(player_name=None, course=None):
    path = missed_file_path(player_name, course)
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_missed(missed, player_name=None, course=None):
    path = missed_file_path(player_name, course)
    os.makedirs(PERSONAL_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(missed, f, ensure_ascii=False, indent=2)


def add_or_reset_missed(missed, word, player_name=None, course=None):
    """通常/タイムアタックで間違えたときに登録・更新する（復習回数は0に戻す）"""
    english = getattr(word, "english", None)
    correct = word.correct_choice()
    for m in missed:
        if m.get("english") == english:
            m["japanese"] = correct
            m["review_count"] = 0
            break
    else:
        missed.append({
            "english": english,
            "japanese": correct,
            "example_en": getattr(word, "example_en", None),
            "example_ja": getattr(word, "example_ja", None),
            "note": getattr(word, "note", None),
            "review_count": 0,
        })
    save_missed(missed, player_name, course)


def update_review_count(missed, english, count, player_name=None, course=None):
    for m in missed:
        if m.get("english") == english:
            m["review_count"] = count
            break
    save_missed(missed, player_name, course)


# -------------------------
# ランキング保存（ローカル・コースごと）
# -------------------------
def load_ranking(course=None, mode_suffix=""):
    path = ranking_file_path(course, mode_suffix)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        # ▼ 過去の不具合等で紛れ込んだ非数値エントリ（例: "error"キー）を除外して自動修復する
        return {p: s for p, s in data.items() if isinstance(s, (int, float)) and not isinstance(s, bool)}
    except:
        return {}


def save_ranking(ranking, course=None, mode_suffix=""):
    path = ranking_file_path(course, mode_suffix)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ranking, f, ensure_ascii=False, indent=2)


def best_score_for_player(player_name):
    """コース(Junior/High)をまたいだ、そのプレイヤーの最高得点を返す（A対応）"""
    best = None
    for c in COURSES:
        rk = load_ranking(c)
        if player_name in rk:
            if best is None or rk[player_name] > best:
                best = rk[player_name]
    return best


# -------------------------
# Firebase 連携
# -------------------------
def firebase_enabled():
    return bool(FIREBASE_DB_URL)


def firebase_get_ranking(course=None, mode_suffix=""):
    if not firebase_enabled():
        return None
    try:
        course = course or st.session_state.get("course") or COURSES[0]
        url = f"{FIREBASE_DB_URL}/ranking_{course}{mode_suffix}.json"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            # ▼ 権限エラーなど（例: ルール未公開）はデータなし扱いにする
            return None
        data = r.json()
        if not isinstance(data, dict):
            return None
        # ▼ Firebaseがエラー内容（例: {"error": "Permission denied"}）を
        #    返してきた場合、それを誤ってスコアとして取り込まないよう、
        #    値が数値になっている項目だけを採用する
        return {p: s for p, s in data.items() if isinstance(s, (int, float)) and not isinstance(s, bool)}
    except:
        return None


def firebase_set_ranking(ranking, course=None, mode_suffix=""):
    if not firebase_enabled():
        return
    try:
        course = course or st.session_state.get("course") or COURSES[0]
        url = f"{FIREBASE_DB_URL}/ranking_{course}{mode_suffix}.json"
        requests.put(url, json=ranking, timeout=5)
    except:
        pass


def merged_ranking(course=None, mode_suffix=""):
    """ローカルのランキングJSONとFirebase（設定されていれば）をマージして返す。

    ★2対応：Streamlit Community Cloudはアプリ再起動でローカルのJSONファイルが
    消えてしまうため、表示時には必ずこの関数を使い、Firebase側に残っている
    記録があればそれをローカルに復元してから返す。
    """
    ranking = load_ranking(course, mode_suffix)
    if firebase_enabled():
        cloud = firebase_get_ranking(course, mode_suffix)
        if cloud:
            changed = False
            for p, score in cloud.items():
                if p not in ranking or score > ranking[p]:
                    ranking[p] = score
                    changed = True
            if changed:
                # ▼ 復元した記録をローカルにも書き戻しておく（次回以降の読み込みを軽くする）
                save_ranking(ranking, course, mode_suffix)
    return ranking


def finalize_time_attack_score(mode_suffix=""):
    """タイムアタックのスコアをランキングに確定保存する（A対応：時間切れ検知直後に必ず呼ぶ）

    mode_suffix="" : 通常（4択）タイムアタック用ランキング
    mode_suffix="_spell" : スペル タイムアタック用ランキング（別ファイルに分離）
    """
    course = st.session_state.get("course")
    ranking = load_ranking(course, mode_suffix)
    player_data = st.session_state.player
    player = player_data["name"] if isinstance(player_data, dict) else player_data
    score = st.session_state.time_score

    if player not in ranking or score > ranking[player]:
        ranking[player] = score
        save_ranking(ranking, course, mode_suffix)
        if firebase_enabled():
            firebase_set_ranking(ranking, course, mode_suffix)
    return ranking


def save_best_score(score, course=None, mode_suffix=""):
    """通常モード／スペル入力モード（タイムアタックでない）など、
    正解するたびに伸びていくスコアを、そのつど自己ベストとしてランキングに
    保存する（1問正解するごとに呼んでよいように、ハイスコア更新時だけ書き込む）。

    タイムアタック系は finalize_time_attack_score() を使うのでこちらは使わない。
    """
    course = course or st.session_state.get("course")
    ranking = load_ranking(course, mode_suffix)
    player_data = st.session_state.player
    player = player_data["name"] if isinstance(player_data, dict) else player_data

    if player not in ranking or score > ranking[player]:
        ranking[player] = score
        save_ranking(ranking, course, mode_suffix)
        if firebase_enabled():
            firebase_set_ranking(ranking, course, mode_suffix)
    return ranking


# -------------------------
# スペル入力モード：出題文生成
# -------------------------
def build_blank_placeholder(english):
    """対象の英単語（複数語の場合はスペース区切り）から、
    頭文字だけ見せて残りを文字数分の空欄にしたプレースホルダーを作る。

    例: "apple" -> "[a____]"
        "How about" -> "[H__ a____]"（単語ごとに区切って、頭文字＋残り文字数分の _ にする）
    """
    parts = (english or "").split(" ")
    blanks = [(p[0] + "_" * (len(p) - 1)) if p else "" for p in parts]
    return "[" + " ".join(blanks) + "]"


def build_spell_prompt(word):
    """スペル入力モード用の出題文を作る。

    example_en があり、その中に対象の英単語が含まれていれば、
    その部分を頭文字＋文字数分の空欄（例: [a____] や [H__ a____]）にした
    例文を返す。
    example_en が無い／単語が見つからない場合でも、単語そのものの
    頭文字＋空欄ヒント（word_hint）は必ず返す。

    戻り値: (japanese_line, blanked_en または None, word_hint または None)
    """
    japanese_line = word.japanese
    blanked = None

    example_en = getattr(word, "example_en", None)
    english = getattr(word, "english", None)
    word_hint = build_blank_placeholder(english) if english else None

    if example_en and english:
        pattern = re.compile(re.escape(english), re.IGNORECASE)
        if pattern.search(example_en):
            placeholder = build_blank_placeholder(english)
            blanked = pattern.sub(lambda m: placeholder, example_en, count=1)
            example_ja = getattr(word, "example_ja", None)
            if example_ja:
                japanese_line = example_ja

    return japanese_line, blanked, word_hint


# -------------------------
# 問題生成
# -------------------------
def next_question():
    # ▼ 現在の単語帳を必ず使う
    words = st.session_state.words
    if not words:
        # ▼ 単語データが無い場合はここで止める（空リストでのrandom.choiceを避ける）
        st.session_state.current = None
        st.session_state.choices = []
        return
    missed = load_missed()

    if st.session_state.mode == "review":
        if not missed:
            st.session_state.mode = "normal"
            word = random.choice(words)
        else:
            m = random.choice(missed)
            word = WordBasic(
                m["english"],
                m["japanese"],
                m.get("example_en"),
                m.get("example_ja"),
                m.get("note")
            )
            # ▼ 復習回数（このセッションで未取得なら保存済みの値を初期値にする）
            st.session_state.review_stats.setdefault(word.english, m.get("review_count", 0))
    elif st.session_state.mode in ("spell", "spell_time"):
        # ▼ スペル入力モード（通常／タイムアタック）は WordBasic（english/japaneseを持つ単語）のみを対象にする
        spell_words = [w for w in words if isinstance(w, WordBasic)]
        st.session_state.spell_words = spell_words
        if not spell_words:
            st.session_state.current = None
            st.session_state.choices = []
            return
        word = random.choice(spell_words)
        st.session_state.current = word
        st.session_state.choices = []
        return
    else:
        word = random.choice(words)

    st.session_state.current = word

    # ▼ 選択肢生成
    if isinstance(word, WordQuiz):
        choices = word.choices.copy()
        random.shuffle(choices)
    else:
        pool = {word.japanese}
        while len(pool) < 4:
            w = random.choice(words)
            if isinstance(w, WordBasic):
                pool.add(w.japanese)
        choices = list(pool)
        random.shuffle(choices)

    st.session_state.choices = choices


# ---------------------------------------------------------
# セッション状態
# ---------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "select"
if "player" not in st.session_state:
    st.session_state.player = None
if "course" not in st.session_state:
    st.session_state.course = None
if "mode" not in st.session_state:
    st.session_state.mode = "menu"
if "current" not in st.session_state:
    st.session_state.current = None
if "choices" not in st.session_state:
    st.session_state.choices = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "total" not in st.session_state:
    st.session_state.total = 0
if "review_stats" not in st.session_state:
    st.session_state.review_stats = {}
if "review_progress" not in st.session_state:
    st.session_state.review_progress = 0
if "time_start" not in st.session_state:
    st.session_state.time_start = None
if "time_score" not in st.session_state:
    st.session_state.time_score = 0
if "time_combo" not in st.session_state:
    st.session_state.time_combo = 0
if "level" not in st.session_state:
    st.session_state.level = 1
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "words" not in st.session_state:
    st.session_state.words = []
if "current_wordlist" not in st.session_state:
    st.session_state.current_wordlist = "words_lv01.csv"
if "spell_words" not in st.session_state:
    st.session_state.spell_words = []
if "spell_seq" not in st.session_state:
    st.session_state.spell_seq = 0
if "spell_awaiting_next" not in st.session_state:
    st.session_state.spell_awaiting_next = False
if "spell_last_result" not in st.session_state:
    st.session_state.spell_last_result = None


def reset_game_state(keep_course=True):
    st.session_state.mode = "menu"
    st.session_state.current = None
    st.session_state.choices = []
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.review_stats = {}
    st.session_state.review_progress = 0
    st.session_state.time_start = None
    st.session_state.time_score = 0
    st.session_state.time_combo = 0
    st.session_state.level = 1
    st.session_state.streak = 0
    st.session_state.current_wordlist = "words_lv01.csv"
    st.session_state.spell_words = []
    st.session_state.spell_seq = 0
    st.session_state.spell_awaiting_next = False
    st.session_state.spell_last_result = None
    if not keep_course:
        st.session_state.course = None


# ---------------------------------------------------------
# 人選択画面
# ---------------------------------------------------------
def page_select():
    st.markdown("<div class='name-title'>だれがやる？</div>", unsafe_allow_html=True)
    st.write("")

    # ▼ ランキングはコースごとに1回だけ取得する（プレイヤーごとに取得し直すと通信回数が
    #   5人×2コース×2種類＝最大20回になってしまい、その分アプリが重くなっていたため）
    rankings_by_course = {
        c: (merged_ranking(c), merged_ranking(c, "_spell"))
        for c in COURSES
    }

    cols = st.columns(3)
    for i, p in enumerate(players):
        with cols[i % 3]:
            # ▼ C対応：中学生／高校生それぞれの「タイムアタック系」最高得点を表示
            #    （通常タイムアタックとスペルタイムアタックのうち高い方を採用）
            score_lines = []
            for c in COURSES:
                ta_normal_rk, ta_spell_rk = rankings_by_course[c]
                ta_normal = ta_normal_rk.get(p["name"])
                ta_spell = ta_spell_rk.get(p["name"])
                candidates = [v for v in (ta_normal, ta_spell) if v is not None]
                best = max(candidates) if candidates else None
                s_text = str(best) if best is not None else "記録なし"
                score_lines.append(f"{COURSE_ICONS[c]}{COURSE_LABELS[c]}: {s_text}")
            score_text = "　".join(score_lines)

            if st.button(p["name"], key=f"player_select_{i}"):
                st.session_state.player = p
                reset_game_state(keep_course=False)
                st.session_state.page = "game"
                st.rerun()

            card_html = f"""
            <div class="pixel-card" style="background-color:{p['color']}">
                <div class="icon">{p['icon']}</div>
                {p['name']}<br>
                <span style="font-size:15px;">{score_text}</span>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown(
        "<div class='tap-guide'>タップして自分の名前を選んでね</div>",
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# コース選択画面（C対応：中学生／高校生）
# ---------------------------------------------------------
def page_course_select():
    player_data = st.session_state.player
    player_name = player_data["name"] if isinstance(player_data, dict) else player_data

    st.markdown(
        f"<div class='name-title' style='font-size:30px;'>{player_name} さん</div>"
        "<div class='tap-guide' style='margin-bottom:10px;'>コースをえらんでね</div>",
        unsafe_allow_html=True
    )

    cols = st.columns(2)
    for i, c in enumerate(COURSES):
        with cols[i]:
            # ★3対応：人選択画面と同じく「タイムアタック（4択／スペルの高い方）」の記録を表示する
            ta_normal = merged_ranking(c).get(player_name)
            ta_spell = merged_ranking(c, "_spell").get(player_name)
            candidates = [v for v in (ta_normal, ta_spell) if v is not None]
            best = max(candidates) if candidates else None
            score_text = f"🏆タイムアタック: {best}" if best is not None else "記録なし"

            if st.button(f"{COURSE_ICONS[c]} {COURSE_LABELS[c]}", key=f"course_select_{c}"):
                st.session_state.course = c
                reset_game_state(keep_course=True)
                st.rerun()

            st.markdown(
                f"""
                <div class="pixel-card" style="background-color:#eef6ff;">
                    <div class="icon">{COURSE_ICONS[c]}</div>
                    {COURSE_LABELS[c]}<br>
                    <span style="font-size:16px;">{score_text}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    if st.button("👤 プレイヤー選択に戻る", key="back_to_select_from_course"):
        st.session_state.page = "select"
        st.session_state.player = None
        st.session_state.course = None
        st.rerun()


def game_menu(words, missed, ranking):
    player_data = st.session_state.player
    player_name = player_data["name"] if isinstance(player_data, dict) else player_data
    course = st.session_state.course

    st.markdown(
        f"""
        <div style='text-align:center; margin-bottom:4px;'>
            <span class='name-title' style='font-size:28px;'>{player_name} さん</span>
        </div>
        <div style='text-align:center; margin-bottom:8px;'>
            <span class='course-badge'>{COURSE_ICONS[course]} {COURSE_LABELS[course]}</span>
            <span class='wordbook-badge'>📘 {st.session_state.current_wordlist}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h3 style='text-align:center; color:#fff; text-shadow:2px 2px 0 rgba(0,0,0,0.2); margin:4px 0;'>モードを選んでね</h3>",
                unsafe_allow_html=True)

    if st.button("通常モード", key="normal_mode"):
        st.session_state.mode = "normal"
        st.session_state.score = 0
        st.session_state.total = 0
        st.session_state.streak = 0
        # ▼ ゲーム開始時は必ずレベル1・最初の単語帳に戻す
        st.session_state.level = 1
        st.session_state.current_wordlist = "words_lv01.csv"
        # ▼ current を None にしておき、次回描画時に「新しい単語帳」から出題させる
        #   （ここで next_question() を呼ぶと、まだ古い単語帳のままなので注意）
        st.session_state.current = None
        st.session_state.choices = []
        st.rerun()

    if st.button(f"復習モード（間違えた単語：{len(missed)}）", key="review_mode"):
        if len(missed) == 0:
            st.warning("まだ復習できる単語がありません")
        else:
            st.session_state.mode = "review"
            st.session_state.review_progress = 0
            next_question()
            st.rerun()

    if st.button("タイムアタック（5分）", key="time_mode"):
        st.session_state.mode = "time"
        st.session_state.time_start = time.time()
        st.session_state.time_score = 0
        st.session_state.time_combo = 0
        st.session_state.streak = 0
        # ▼ ゲーム開始時は必ずレベル1・最初の単語帳に戻す
        st.session_state.level = 1
        st.session_state.current_wordlist = "words_lv01.csv"
        st.session_state.current = None
        st.session_state.choices = []
        st.rerun()

    if st.button("✏️ スペル入力モード", key="spell_mode"):
        st.session_state.mode = "spell"
        st.session_state.score = 0
        st.session_state.total = 0
        st.session_state.streak = 0
        # ▼ ゲーム開始時は必ずレベル1・最初の単語帳に戻す
        st.session_state.level = 1
        st.session_state.current_wordlist = "words_lv01.csv"
        st.session_state.current = None
        st.session_state.choices = []
        st.session_state.spell_seq = 0
        st.session_state.spell_awaiting_next = False
        st.session_state.spell_last_result = None
        st.rerun()

    if st.button("✏️⏱️ スペル タイムアタック（5分）", key="spell_time_mode"):
        st.session_state.mode = "spell_time"
        st.session_state.time_start = time.time()
        st.session_state.time_score = 0
        st.session_state.time_combo = 0
        st.session_state.streak = 0
        # ▼ ゲーム開始時は必ずレベル1・最初の単語帳に戻す
        st.session_state.level = 1
        st.session_state.current_wordlist = "words_lv01.csv"
        st.session_state.current = None
        st.session_state.choices = []
        st.session_state.spell_seq = 0
        st.session_state.spell_awaiting_next = False
        st.session_state.spell_last_result = None
        st.rerun()

    rows = "".join(
        f"<div style='display:flex; justify-content:space-between; padding:3px 0;'>"
        f"<span>{'🥇🥈🥉'[i:i+1] if i < 3 else '　'} {p}</span><span>{s}点</span></div>"
        for i, (p, s) in enumerate(sorted(ranking.items(), key=lambda x: -x[1]))
    ) or "<div style='color:#888;'>まだ記録がありません</div>"

    st.markdown(
        f"""
        <div class="score-panel" style="margin-top:10px;">
            <div style="font-weight:900; margin-bottom:4px;">🏆 {COURSE_LABELS[course]}ランキング</div>
            {rows}
        </div>
        """,
        unsafe_allow_html=True
    )

    spell_ranking = merged_ranking(course, "_spell")
    spell_rows = "".join(
        f"<div style='display:flex; justify-content:space-between; padding:3px 0;'>"
        f"<span>{'🥇🥈🥉'[i:i+1] if i < 3 else '　'} {p}</span><span>{s}点</span></div>"
        for i, (p, s) in enumerate(sorted(spell_ranking.items(), key=lambda x: -x[1]))
    ) or "<div style='color:#888;'>まだ記録がありません</div>"

    st.markdown(
        f"""
        <div class="score-panel" style="margin-top:6px;">
            <div style="font-weight:900; margin-bottom:4px;">🏆✏️ {COURSE_LABELS[course]}スペル タイムアタックランキング</div>
            {spell_rows}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔀 コース変更", key="change_course"):
            reset_game_state(keep_course=False)
            st.rerun()
    with col_b:
        if st.button("👤 プレイヤー選択に戻る", key="back_to_select"):
            st.session_state.page = "select"
            st.session_state.player = None
            st.session_state.course = None
            st.rerun()


def page_game():
    # ▼ C対応：コース未選択ならコース選択画面へ
    if st.session_state.course is None:
        page_course_select()
        return

    course = st.session_state.course

    # ▼ 現在の単語帳を毎回読み込む（これが重要）
    filename = os.path.join(get_word_dir(course), st.session_state.current_wordlist)
    st.session_state.words = load_words(filename)
    words = st.session_state.words
    missed = load_missed()

    # ▼ 単語データが無い場合はメニュー表示より先にチェックする
    #    （メニューの各モードボタンが next_question() を呼び、
    #      空リストで random.choice するとcrashするため）
    if not words:
        st.warning(f"{COURSE_LABELS[course]}の単語データ（{st.session_state.current_wordlist}）が見つかりません。"
                    f"Word_Data/{course}/ フォルダにCSVを入れてください。")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔀 コース変更", key="change_course_no_words"):
                reset_game_state(keep_course=False)
                st.rerun()
        with col_b:
            if st.button("👤 プレイヤー選択に戻る", key="back_no_words"):
                st.session_state.page = "select"
                st.session_state.player = None
                st.session_state.course = None
                st.rerun()
        return

    if st.session_state.mode == "menu":
        # ▼ ランキング（Firebaseとのマージ）はメニュー表示時だけ取得する。
        #   クイズ回答のたびの再描画で毎回通信すると重くなるため。
        ranking = merged_ranking(course)
        game_menu(words, missed, ranking)
        return

    # 問題・回答画面
    # -------------------------
    # 問題表示
    # -------------------------
    word = st.session_state.current

    if word is None:
        next_question()
        word = st.session_state.current

    # ▼ スペル入力モードで出題できる単語が無い場合はここで止める
    if word is None:
        if st.session_state.mode in ("spell", "spell_time"):
            st.warning("この単語帳にはスペル入力できる単語がありません。")
        else:
            st.warning("出題できる単語がありません。")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⬅️ もどる", key="back_to_menu_no_word"):
                st.session_state.mode = "menu"
                st.rerun()
        with col_b:
            if st.button("🔀 コース変更", key="change_course_no_word"):
                reset_game_state(keep_course=False)
                st.rerun()
        return

    col_back, col_level = st.columns([1, 3])
    with col_back:
        if st.button("⬅️ もどる", key="back_to_menu_ingame"):
            st.session_state.mode = "menu"
            st.rerun()
    with col_level:
        st.markdown(
            f"<div style='text-align:right;'>"
            f"<span class='level-badge'>Lv.{st.session_state.level}</span> "
            f"<span class='wordbook-badge'>📘 {st.session_state.current_wordlist}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # -------------------------
    # スペル入力モード（通常／タイムアタック共通）
    # 日本語の意味 → 英単語のスペルを入力する
    # -------------------------
    if st.session_state.mode in ("spell", "spell_time"):
        is_time_attack = st.session_state.mode == "spell_time"

        japanese_line, blanked_en, word_hint = build_spell_prompt(word)
        spell_hint_text = blanked_en or word_hint
        spell_example_html = f"<div class='example'>✏️ {spell_hint_text}</div>" if spell_hint_text else ""

        st.markdown(
            f"""
            <div class="question-card">
                <div style="font-size:14px; color:#888; font-weight:700;">問題（日本語の意味）</div>
                <div class="en" style="font-size:28px;">{japanese_line}</div>
                {spell_example_html}
            </div>
            """,
            unsafe_allow_html=True
        )
        effect_placeholder = st.empty()

        if st.session_state.spell_awaiting_next:
            # ▼ 不正解のときは、正解のスペルを表示したまま「次へ」を押すまで進めない
            result = st.session_state.spell_last_result or {}
            if result.get("correct"):
                st.success(result.get("message", "正解！"))
                effect_placeholder.markdown(show_effect("correct", 0), unsafe_allow_html=True)
            else:
                st.error(result.get("message", "不正解…"))
                effect_placeholder.markdown(show_effect("wrong", 0), unsafe_allow_html=True)

            if st.button("👉 次の問題へ", key=f"spell_next_{st.session_state.spell_seq}"):
                st.session_state.spell_awaiting_next = False
                st.session_state.spell_last_result = None
                st.session_state.spell_seq += 1
                next_question()
                st.rerun()

        else:
            with st.form(key=f"spell_form_{st.session_state.spell_seq}", clear_on_submit=True):
                user_input = st.text_input(
                    "スペルを入力してね（英語）",
                    key=f"spell_input_{st.session_state.spell_seq}"
                )
                submitted = st.form_submit_button("こたえる")

            # ▼ D対応：入力欄に自動でカーソルを合わせる（毎回クリックしなくて良いようにする）
            #    ・setTimeout一発だけだと、問題2問目以降は要素の描画が
            #      間に合わずフォーカスに失敗することがあるため、
            #      見つかるまで繰り返し探す方式にする。
            #    ・スクリプトの中身に spell_seq を埋め込み、
            #      前回と完全に同じHTMLにならないようにする
            #      （同一内容だとブラウザ/Streamlit側でiframeの
            #        再実行がスキップされることがあるため）。
            components.html(
                f"""
                <script>
                (function () {{
                    const targetLabel = "スペルを入力してね（英語）";
                    function tryFocus() {{
                        const doc = window.parent.document;
                        const inputs = doc.querySelectorAll('input[type="text"]');
                        for (const el of inputs) {{
                            if (el.getAttribute('aria-label') === targetLabel) {{
                                el.focus();
                                return true;
                            }}
                        }}
                        return false;
                    }}
                    if (tryFocus()) {{ return; }}
                    let tries = 0;
                    const timer = setInterval(function () {{
                        tries += 1;
                        if (tryFocus() || tries > 40) {{
                            clearInterval(timer);
                        }}
                    }}, 100);
                }})();
                </script>
                <!-- spell_seq:{st.session_state.spell_seq} -->
                """,
                height=0,
            )

            if submitted:
                if is_time_attack:
                    elapsed = time.time() - st.session_state.time_start
                    if elapsed >= 300:
                        finalize_time_attack_score(mode_suffix="_spell")
                        st.session_state.mode = "menu"
                        st.rerun()

                correct = word.english or ""
                st.session_state.total += 1
                is_correct = user_input.strip().lower() == correct.strip().lower()

                if is_correct:
                    st.session_state.streak += 1
                    if is_time_attack:
                        st.session_state.time_combo += 1
                        bonus = st.session_state.time_combo // 5
                        gained = 1 + bonus
                        st.session_state.time_score += gained
                        # ★2対応：5分経過を待たず、1問ごとにその場でランキングJSONへ保存する
                        save_best_score(st.session_state.time_score, course, mode_suffix="_spell")
                        message = f"正解！ +{gained}点（コンボ x{st.session_state.time_combo}）"
                    else:
                        st.session_state.score += 1
                        save_best_score(st.session_state.score, course, mode_suffix="_spell_normal")
                        message = "正解！"

                    play_sound(SOUND_CORRECT_PATH)

                    if st.session_state.streak >= STREAK_TO_LEVEL_UP:
                        st.session_state.streak = 0
                        st.session_state.level += 1

                        # ★ Lv1 と Lv2 を交互に切り替える(Junior)
                        if course == "Junior":
                            stage = (st.session_state.level - 1) % 2
                        elif course == "High":
                            stage = (st.session_state.level - 1) % 8
                        else:
                            stage = 0  # デフォルト（念のため）

                        spell_filename = os.path.join(get_word_dir(course), f"words_lv{stage + 1:02d}.csv")
                        if os.path.exists(spell_filename):
                            new_words = load_words(spell_filename)
                            if new_words:
                                st.session_state.words = new_words
                                st.session_state.current_wordlist = os.path.basename(spell_filename)
                                message += f"／単語帳を {st.session_state.current_wordlist} に変更しました"

                    # ▼ 正解のときはテンポよく次の問題へ進む（効果音が鳴りきるまで少し待つ）
                    st.success(message)
                    effect_placeholder.empty()
                    effect_placeholder.markdown(show_effect("correct", 0), unsafe_allow_html=True)
                    time.sleep(1.0)
                    st.session_state.spell_seq += 1
                    next_question()
                    effect_placeholder.empty()
                    st.rerun()

                else:
                    st.session_state.streak = 0
                    add_or_reset_missed(missed, word)
                    play_sound(SOUND_WRONG_PATH)

                    if is_time_attack:
                        st.session_state.time_combo = 0
                        st.session_state.time_score -= 1
                        # ★2対応：5分経過を待たず、1問ごとにその場でランキングJSONへ保存する
                        save_best_score(st.session_state.time_score, course, mode_suffix="_spell")

                    # ▼ E対応：不正解のときは正解のスペルを表示したまま止め、
                    #    「次の問題へ」ボタンを押すまで自動では進めない
                    #    （rerun前に少し待つことで、効果音が鳴りきる前にiframeが
                    #      消えてしまうのを防ぐ）
                    st.session_state.spell_last_result = {
                        "correct": False,
                        "message": f"不正解… 正解は「{correct}」",
                    }
                    time.sleep(1.0)
                    st.session_state.spell_awaiting_next = True
                    st.rerun()

        # -------------------------
        # スコア表示
        # -------------------------
        if is_time_attack:
            elapsed = time.time() - st.session_state.time_start
            remain = max(0, 300 - int(elapsed))
            st.markdown(
                f"<div class='score-panel'>⏱️ 残り時間：{remain//60}:{remain%60:02d}"
                f"　｜　スコア：{st.session_state.time_score}"
                f"　｜　コンボ：x{st.session_state.time_combo}</div>",
                unsafe_allow_html=True
            )
            # ▼ 回答待ち（正解表示中）でなければ、時間切れをここでも確定保存する
            if remain <= 0 and not st.session_state.spell_awaiting_next:
                finalize_time_attack_score(mode_suffix="_spell")
                st.session_state.mode = "menu"
                st.rerun()
        else:
            st.markdown(
                f"<div class='score-panel'>✅ 正解数：{st.session_state.score} / {st.session_state.total}</div>",
                unsafe_allow_html=True
            )
        return

    example_html = ""
    if getattr(word, "example_en", None):
        example_html += f"<div class='example'>✏️ {word.example_en}</div>"
    # if getattr(word, "example_ja", None):
    #     example_html += f"<div class='example'>✏️ {word.example_ja}</div>"

    st.markdown(
        f"""
        <div class="question-card">
            <div style="font-size:14px; color:#888; font-weight:700;">問題</div>
            <div class="en">{word.prompt()}</div>
            {example_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    effect_placeholder = st.empty()

    # -------------------------
    # 選択肢
    # -------------------------
    for _choice_i, c in enumerate(st.session_state.choices):
        if st.button(c, key=f"choice_btn_{_choice_i}"):
            correct = word.correct_choice()
            st.session_state.total += 1

            # -------------------------
            # 通常モード（レベルアップ対応）
            # -------------------------
            if st.session_state.mode == "normal":
                if c == correct:
                    st.session_state.score += 1
                    st.session_state.streak += 1
                    save_best_score(st.session_state.score, course, mode_suffix="_normal")
                    st.success("正解！")
                    # 演出＋効果音（共通化）
                    effect_placeholder.empty()
                    effect_html = show_effect("correct", 0)
                    effect_placeholder.markdown(effect_html, unsafe_allow_html=True)
                    play_sound(SOUND_CORRECT_PATH)

                    if st.session_state.streak >= STREAK_TO_LEVEL_UP:
                        st.session_state.streak = 0
                        st.session_state.level += 1

                        # ★画面揺れアニメーション
                        effect_placeholder.markdown(show_effect("levelup",0),unsafe_allow_html=True)   

                        # ★ Lv1 と Lv2 を交互に切り替える(Junior)
                        if course == "Junior":
                            stage = (st.session_state.level - 1) % 2
                        elif course == "High":
                            stage = (st.session_state.level - 1) % 8
                        else:
                            stage = 0  # デフォルト（念のため）                        

                        filename = os.path.join(get_word_dir(course), f"words_lv{stage + 1:02d}.csv")

                        if os.path.exists(filename):
                            new_words = load_words(filename)
                            if new_words:
                                # words[:] = new_words
                                st.session_state.words = new_words  # ← これが重要！
                                st.session_state.current_wordlist = os.path.basename(filename)
                                st.info(f"単語帳を {st.session_state.current_wordlist} に変更しました")

                else:
                    st.error(f"不正解… 正解は「{correct}」")
                    st.session_state.streak = 0
                    add_or_reset_missed(missed, word)
                    # 演出＋効果音（共通化）
                    effect_placeholder.empty()
                    effect_html = show_effect("wrong", 0)
                    effect_placeholder.markdown(effect_html, unsafe_allow_html=True)
                    play_sound(SOUND_WRONG_PATH)
                time.sleep(0.5)                   

            # -------------------------
            # 復習モード
            # -------------------------
            elif st.session_state.mode == "review":
                if c == correct:
                    st.session_state.review_stats[word.english] = st.session_state.review_stats.get(word.english, 0) + 1
                    update_review_count(missed, word.english, st.session_state.review_stats[word.english])
                    # 演出＋効果音（共通化）
                    effect_placeholder.empty()
                    effect_html = show_effect("correct", st.session_state.review_stats[word.english])
                    effect_placeholder.markdown(effect_html, unsafe_allow_html=True)
                    play_sound(SOUND_CORRECT_PATH)
                    time.sleep(0.5)

                    # 5回連続正解で卒業
                    if st.session_state.review_stats[word.english] >= 5:
                        st.success(f"『{word.english}』を復習卒業！")
                        time.sleep(0.5)
                        missed[:] = [m for m in missed if m["english"] != word.english]
                        save_missed(missed)

                        # ▼ 復習する単語がもうなければ、そのままモード選択に戻す
                        if not missed:
                            st.balloons()
                            st.info("復習する単語がなくなりました！モード選択にもどります")
                            time.sleep(1.2)
                            st.session_state.mode = "menu"
                            st.session_state.current = None
                            st.session_state.choices = []
                            st.rerun()
                else:
                    st.error(f"不正解… 正解は「{correct}」")
                    st.session_state.review_stats[word.english] = 0
                    update_review_count(missed, word.english, 0)
                    # 演出＋効果音（共通化）
                    effect_placeholder.empty()
                    effect_html = show_effect("wrong", 0)
                    effect_placeholder.markdown(effect_html, unsafe_allow_html=True)
                    play_sound(SOUND_WRONG_PATH)
                    

                st.session_state.review_progress += 1
                if st.session_state.review_progress >= 10:
                    st.info("復習10問おつかれさま！タイトルにもどります")
                    time.sleep(1.0)
                    reset_game_state(keep_course=False)
                    st.session_state.page = "select"
                    st.session_state.player = None
                    st.rerun()

                time.sleep(0.5)  

            # -------------------------
            # タイムアタック
            # -------------------------
            elif st.session_state.mode == "time":
                elapsed = time.time() - st.session_state.time_start
                if elapsed >= 300:
                    # ★A対応：メニューに戻る前に必ずスコアを確定保存する
                    #   （以前はここで先にmenuへ戻ってしまい、ランキングが保存されないバグだった）
                    finalize_time_attack_score()
                    st.session_state.mode = "menu"
                    st.rerun()

                if c == correct:
                    st.session_state.time_combo += 1
                    bonus = st.session_state.time_combo // 5
                    st.session_state.time_score += 1 + bonus
                    st.success(f"正解！ +{1+bonus}点（コンボ x{st.session_state.time_combo}）")
                    # 演出＋効果音（共通化）
                    effect_placeholder.empty()
                    effect_html = show_effect("correct", 0)
                    effect_placeholder.markdown(effect_html, unsafe_allow_html=True)
                    play_sound(SOUND_CORRECT_PATH)

                    # ★タイムアタックでもレベルアップさせる
                    st.session_state.streak += 1

                    if st.session_state.streak >= STREAK_TO_LEVEL_UP:
                        st.session_state.streak = 0
                        st.session_state.level += 1

                        # ★画面揺れアニメーション
                        effect_placeholder.markdown(show_effect("levelup",0),unsafe_allow_html=True)   

                        # ★単語帳切り替え（通常モードと同じ）
                        # ★ Lv1 と Lv2 を交互に切り替える(Junior)
                        if course == "Junior":
                            stage = (st.session_state.level - 1) % 2
                        elif course == "High":
                            stage = (st.session_state.level - 1) % 8
                        else:
                            stage = 0  # デフォルト（念のため）   

                        filename = os.path.join(get_word_dir(course), f"words_lv{stage + 1:02d}.csv")
                        if os.path.exists(filename):
                            new_words = load_words(filename)
                            if new_words:
                                st.session_state.words = new_words
                                st.session_state.current_wordlist = os.path.basename(filename)
                                st.info(f"単語帳を {st.session_state.current_wordlist} に変更しました")

                else:
                    st.session_state.time_combo = 0
                    st.session_state.time_score -= 1
                    st.session_state.streak = 0
                    st.error(f"不正解… 正解は「{correct}」")
                    # 演出＋効果音（共通化）
                    effect_placeholder.empty()
                    effect_html = show_effect("wrong", 0)
                    effect_placeholder.markdown(effect_html, unsafe_allow_html=True)
                    play_sound(SOUND_WRONG_PATH)

                # ★2対応：5分経過を待たず、1問ごとにその場でランキングJSONへ保存する
                #   （5分経過時にしか保存していなかったため、最後までやらないと
                #     ranking_<コース>.json が作られない問題があった）
                save_best_score(st.session_state.time_score, course)
                time.sleep(0.5)  

            next_question()
            effect_placeholder.empty()
            st.rerun()


    # -------------------------
    # スコア表示
    # -------------------------
    if st.session_state.mode == "normal":
        st.markdown(
            f"<div class='score-panel'>✅ 正解数：{st.session_state.score} / {st.session_state.total}</div>",
            unsafe_allow_html=True
        )

    elif st.session_state.mode == "review":
        word_count = st.session_state.review_stats.get(getattr(word, "english", ""), 0)
        st.markdown(
            f"<div class='score-panel'>📚 セット進捗：{st.session_state.review_progress}/10"
            f"　｜　この単語の連続正解：{word_count}/5</div>",
            unsafe_allow_html=True
        )

    elif st.session_state.mode == "time":
        elapsed = time.time() - st.session_state.time_start
        remain = max(0, 300 - int(elapsed))
        st.markdown(
            f"<div class='score-panel'>⏱️ 残り時間：{remain//60}:{remain%60:02d}"
            f"　｜　スコア：{st.session_state.time_score}"
            f"　｜　コンボ：x{st.session_state.time_combo}</div>",
            unsafe_allow_html=True
        )

        # 終了処理（A対応：ボタン操作なしで時間切れになった場合の保険）
        if remain <= 0:
            finalize_time_attack_score()
            st.session_state.mode = "menu"
            st.rerun()

# ---------------------------------------------------------
# ページ遷移
# ---------------------------------------------------------
if st.session_state.page == "select":
    page_select()
elif st.session_state.page == "game":
    page_game()
