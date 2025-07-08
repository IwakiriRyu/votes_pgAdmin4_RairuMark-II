from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
from psycopg2 import Error
import hashlib, base64, secrets
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
db_url = os.environ.get("DATABASE_URL")

# ✅ 修正済み get_db 関数
def get_db():
    conn = psycopg2.connect(db_url, sslmode='require')
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn, cursor

# パスワード管理
def hash_password(password):
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 310000)
    return f"pbkdf2_sha256$310000${salt}${base64.b64encode(pw_hash).decode()}"

def verify_password(password, password_hash): 
    try:
        algorithm, iterations, salt, hashed = password_hash.split('$', 3)
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
        return base64.b64encode(new_hash).decode() == hashed
    except Exception:
        return False

# ホーム画面
@app.route("/") 
def home():
    user_id = session.get('user_id')
    return render_template("home.html", user_id=user_id)

# クイズ画面
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if 'user_id' not in session:
        flash("ログインしてください。")
        return redirect(url_for('login'))
    
    conn, cursor = get_db()
    
    if 'question_count' not in session:
        session['question_count'] = 0
        session['score'] = 0
    
    if request.method == "POST":
        question_id = request.form.get('question_id')
        selected_option = request.form.get('option')
        cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = cursor.fetchone()

        if question:
            correct = selected_option == question['answer']
            session['score'] += 1 if correct else 0
            feedback = "正解！" if correct else "不正解！"
            explanation = question['explanation']
            session['question_count'] += 1
            
            cursor.close()
            conn.close()
            return render_template("result.html", feedback=feedback, explanation=explanation, question_count=session['question_count'] - 1)
    
    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    question = cursor.fetchone()
    options = [question['option1'], question['option2'], question['option3'], question['option4']]
    
    cursor.close()
    conn.close()
    return render_template("quiz.html", question=question['title'], options=options, question_id=question['id'], question_count=session['question_count'])

# リザルト画面
@app.route("/score")
def results():
    score = session.pop('score', 0)
    session.pop('question_count', None)
    return render_template("score.html", score=score)

# 次の問題へ
@app.route("/next_question", methods=["POST"])
def next_question():
    if session['question_count'] == 10:
        return redirect(url_for('results'))
    return redirect(url_for('quiz'))

# ログイン画面
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("ユーザー名とパスワードが必要です。")
            return render_template("login.html", error_message="入力ができていません。")

        conn, cursor = get_db()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and verify_password(password, user['password']):
            session['user_id'] = user['id']
            flash("ログインしました！")
            return redirect(url_for('home'))
        else:
            flash("ユーザー名またはパスワードが間違っています。")
            return render_template("login.html", error_message="ログイン失敗。")
    return render_template("login.html")

# 新規登録画面
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template("touroku.html", error_message="全て入力してください。")

        try:
            conn, cursor = get_db()
            password_hash = hash_password(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                           (username, password_hash))
            conn.commit()
            flash("登録が完了しました。ログインしてください。")
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        except psycopg2.Error as err:
            conn.rollback()
            if err.pgcode == '23505':  # Unique violation
                cursor.close()
                conn.close()
                return render_template("touroku.html", error_message="ユーザー名は既に使用されています。")
            raise err
        except Exception as e:
            cursor.close()
            conn.close()
            raise e

    return render_template("touroku.html")

if __name__ == "__main__":
    app.run(debug=True)
