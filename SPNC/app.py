from flask import Flask, render_template, request, redirect, session, flash
import pyodbc
import json

app = Flask(__name__)
app.secret_key = "secret"


conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER= DESKTOP-NI7S795;"
    "DATABASE=gamified_lms;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()


@app.route("/")
def home():

    session.clear()   # xoá session cũ

    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
        )

        user = cursor.fetchone()

        if user:

            session["user"] = user.username
            session["role"] = user.role

            if user.role == "teacher":
                return redirect("/teacher")

            else:
                return redirect("/dashboard")

        else:
            flash("Sai thông tin đăng nhập","danger")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM courses
    """)
    courses = cursor.fetchall()

    cursor.execute("""
    SELECT homework.*, lessons.title AS lesson_title
    FROM homework
    JOIN lessons ON homework.lesson_id = lessons.id
    ORDER BY due_date
    """)
    homeworks = cursor.fetchall()

    xp = user.xp
    level_xp = user.level * 100
    progress = int((xp / level_xp) * 100)

    return render_template(
        "dashboard.html",
        user=user,
        courses=courses,
        homeworks=homeworks,
        progress=progress
    )

@app.route("/course/<course_id>")
def student_course(course_id):

    cursor.execute(
        "SELECT * FROM topics WHERE course_id=?",
        (course_id,)
    )
    topics = cursor.fetchall()

    lessons_by_topic = {}

    for topic in topics:

        cursor.execute(
            "SELECT * FROM lessons WHERE topic_id=?",
            (topic.id,)
        )

        lessons_by_topic[topic.id] = cursor.fetchall()

    return render_template(
        "student_course.html",
        topics=topics,
        lessons_by_topic=lessons_by_topic
    )

import json

@app.route("/lesson/<int:lesson_id>")
def lesson(lesson_id):

    cursor.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
    lesson = cursor.fetchone()

    cursor.execute("SELECT * FROM lesson_contents WHERE lesson_id=?", (lesson_id,))
    contents = cursor.fetchall()

    cursor.execute("SELECT * FROM games WHERE lesson_id=?", (lesson_id,))
    games_raw = cursor.fetchall()

    games = []

    for g in games_raw:
        games.append({
            "id": g.id,
            "type": g.type,
            "question": g.question,
            "data": json.loads(g.data_json) if g.data_json else {}
        })

    return render_template(
        "lesson.html",
        lesson=lesson,
        contents=contents,
        games=games
    )

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        if user:
            flash("Tên tài khoản đã tồn tại", "error")
            return redirect("/register")

        cursor.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username,password)
        )

        conn.commit()

        flash("Đăng ký thành công, mời đăng nhập", "success")

        return redirect("/login")

    return render_template("register.html")

@app.route("/teacher")
def teacher_dashboard():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "teacher":
        return redirect("/dashboard")

    cursor.execute(
    """
    SELECT username,xp,level
    FROM users
    WHERE role='student'
    """
    )

    students = cursor.fetchall()

    data = []

    for s in students:

        xp_next = s.level * 100
        progress = int((s.xp / xp_next) * 100)

        data.append({
            "username": s.username,
            "xp": s.xp,
            "level": s.level,
            "progress": progress
        })

    return render_template(
        "teacher_dashboard.html",
        students=data
    )


@app.route("/logout")
def logout():

    session.clear()

    flash("Đã đăng xuất thành công", "success")

    return redirect("/login")

@app.route("/teacher/courses")
def teacher_courses():

    cursor.execute("SELECT * FROM courses")

    courses = cursor.fetchall()

    return render_template(
        "teacher_courses.html",
        courses=courses
    )

@app.route("/teacher/add_course", methods=["POST"])
def add_course():

    title = request.form["title"]
    description = request.form["description"]

    cursor.execute(
    "INSERT INTO courses(title,description) VALUES (?,?)",
    (title,description)
    )

    conn.commit()

    return redirect("/teacher/courses")

@app.route("/teacher/add_topic", methods=["POST"])
def add_topic():

    course_id = request.form["course_id"]
    title = request.form["title"]

    print("COURSE ID =", course_id)

    cursor.execute(
        "INSERT INTO topics(course_id,title) VALUES (?,?)",
        (course_id,title)
    )

    conn.commit()

    return redirect("/teacher/course/" + course_id)

@app.route("/teacher/add_lesson", methods=["POST"])
def add_lesson():

    topic_id = request.form["topic_id"]
    title = request.form["title"]
    xp = request.form["xp"]

    cursor.execute(
        """
        INSERT INTO lessons(topic_id,title,xp_reward)
        VALUES (?,?,?)
        """,
        (topic_id,title,xp)
    )

    conn.commit()

    return redirect(request.referrer)

@app.route("/teacher/course/<course_id>")
def teacher_course(course_id):

    cursor.execute(
        "SELECT * FROM topics WHERE course_id=?",
        (course_id,)
    )

    topics = cursor.fetchall()

    lessons_by_topic = {}

    for topic in topics:

        cursor.execute(
            "SELECT * FROM lessons WHERE topic_id=?",
            (topic.id,)
        )

        lessons_by_topic[topic.id] = cursor.fetchall()

    return render_template(
        "teacher_course_detail.html",
        topics=topics,
        lessons_by_topic=lessons_by_topic,
        course_id=course_id
    )

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

from flask import redirect, url_for

@app.route("/teacher/upload_content", methods=["POST"])
def upload_content():

    file = request.files.get("file")
    lesson_id = request.form.get("lesson_id")

    if not file:
        return "No file", 400

    filename = secure_filename(file.filename)

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    db_path = "uploads/" + filename

    ext = filename.rsplit(".", 1)[-1].lower()

    if ext in ["mp4", "mov", "avi"]:
        content_type = "video"
    elif ext in ["pdf"]:
        content_type = "pdf"
    elif ext in ["png", "jpg", "jpeg", "webp"]:
        content_type = "image"
    else:
        content_type = "file"

    cursor.execute("""
        INSERT INTO lesson_contents (lesson_id, file_path, content_type)
        VALUES (?, ?, ?)
    """, (lesson_id, db_path, content_type))

    conn.commit()

    
    return redirect(url_for("teacher_lesson", lesson_id=lesson_id))

@app.route("/teacher/delete_content/<int:content_id>", methods=["POST"])
def delete_content(content_id):

    cursor.execute("SELECT file_path FROM lesson_contents WHERE id=?", (content_id,))
    row = cursor.fetchone()

    if row:
        file_path = os.path.join("static", row.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    cursor.execute("DELETE FROM lesson_contents WHERE id=?", (content_id,))
    conn.commit()

    return redirect(request.referrer)

def calculate_level(xp):

    level = 1
    xp_needed = 100

    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = level * 100

    return level

@app.route("/complete_lesson/<lesson_id>")
def complete_lesson(lesson_id):

    user = session["user"]

    cursor.execute(
        "SELECT id,xp FROM users WHERE username=?",
        (user,)
    )

    user_data = cursor.fetchone()

    cursor.execute(
        "SELECT xp_reward FROM lessons WHERE id=?",
        (lesson_id,)
    )

    lesson = cursor.fetchone()

    new_xp = user_data.xp + lesson.xp_reward

    new_level = calculate_level(new_xp)

    cursor.execute(
        """
        UPDATE users
        SET xp=?, level=?
        WHERE id=?
        """,
        (new_xp,new_level,user_data.id)
    )

    conn.commit()

    return redirect("/dashboard")

@app.route("/submit_game", methods=["POST"])
def submit_game():

    data = request.get_json()

    xp = data["xp"]
    game_id = data["game_id"]
    correct = data["correct"]   # 👈 thêm

    username = session["user"]

    
    cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()

    
    cursor.execute("""
    INSERT INTO game_results (user_id, game_id, is_correct)
    VALUES (?, ?, ?)
    """, (user.id, game_id, correct))

    
    if correct:
        cursor.execute("""
        UPDATE users
        SET xp = xp + ?
        WHERE id=?
        """, (xp, user.id))

    conn.commit()

    return {"message": "Saved"}


# @app.route("/teacher/create_game", methods=["POST"])
# def create_game():

#     lesson_id = request.form["lesson_id"]
#     type = request.form["type"]
#     xp = request.form["xp_reward"]

#     question = request.form.get("question","")

#     data = {}

#     if type == "quiz":

#         data = {
#             "A": request.form["A"],
#             "B": request.form["B"],
#             "C": request.form["C"],
#             "D": request.form["D"],
#             "answer": request.form["answer"]
#         }

#     if type == "fill":

#         data = {
#             "answer": request.form["answer"]
#         }

#     if type == "match":

#         data = {
#             "pairs":[
#                 [request.form["left1"], request.form["right1"]],
#                 [request.form["left2"], request.form["right2"]]
#             ]
#         }

#     if type == "order":

#         data = {
#             "line1": request.form["line1"],
#             "line2": request.form["line2"]
#         }

#     if type == "boss":

#         data = {
#             "answer": request.form["answer"]
#         }

#     cursor.execute(

#     """
#     INSERT INTO games
#     (lesson_id,type,question,data_json,xp_reward)
#     VALUES (?,?,?,?,?)
#     """,

#     (
#         lesson_id,
#         type,
#         question,
#         json.dumps(data),
#         xp
#     )

#     )

#     conn.commit()

#     return redirect(request.referrer)

@app.route("/teacher/create_game/<lesson_id>", methods=["POST"])
def create_game(lesson_id):

    game_type = request.form["type"]
    question = request.form.get("question", "")
    xp = request.form.get("xp", 10)

    data = {}

    if game_type == "quiz":
        data = {
            "options": [
                request.form["opt1"],
                request.form["opt2"],
                request.form["opt3"],
                request.form["opt4"]
            ],
            "correct": request.form["correct"]
        }

    elif game_type == "fill":
        data = {
            "answer": request.form["answer"]
        }

    elif game_type == "match":
        data = {
            "left": request.form.getlist("left[]"),
            "right": request.form.getlist("right[]")
        }

    elif game_type == "order":
        data = {
            "lines": request.form.getlist("lines[]")
        }

    elif game_type == "boss":
        data = {
            "answer": request.form["answer"]
        }

    cursor.execute("""
    INSERT INTO games (lesson_id, type, question, data_json, xp_reward)
    VALUES (?, ?, ?, ?, ?)
    """,
    (lesson_id, game_type, question, json.dumps(data), xp)
    )

    conn.commit()

    return redirect("/teacher/lesson/" + lesson_id)

def create_game_page(lesson_id):
    return render_template(
        "teacher_create_game.html",
        lesson_id=lesson_id
    )

@app.route("/teacher/create_game/<lesson_id>")
def create_game_page(lesson_id):
    return render_template(
        "teacher_create_game.html",
        lesson_id=lesson_id
    )

@app.route("/teacher/edit_course/<course_id>", methods=["GET","POST"])
def edit_course(course_id):

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        cursor.execute(
        """
        UPDATE courses
        SET title=?, description=?
        WHERE id=?
        """,
        (title,description,course_id)
        )

        conn.commit()

        return redirect("/teacher/courses")

    cursor.execute(
        "SELECT * FROM courses WHERE id=?",
        (course_id,)
    )

    course = cursor.fetchone()

    return render_template(
        "edit_course.html",
        course=course
    )
    
@app.route("/teacher/delete_course/<course_id>")
def delete_course(course_id):

   
    cursor.execute("DELETE FROM games WHERE lesson_id IN (SELECT id FROM lessons WHERE topic_id IN (SELECT id FROM topics WHERE course_id=?))",(course_id,))
    
    cursor.execute("DELETE FROM lessons WHERE topic_id IN (SELECT id FROM topics WHERE course_id=?)",(course_id,))
    
    cursor.execute("DELETE FROM topics WHERE course_id=?",(course_id,))
    
    cursor.execute("DELETE FROM courses WHERE id=?",(course_id,))

    conn.commit()

    return redirect("/teacher/courses")

@app.route("/teacher/edit_lesson/<lesson_id>", methods=["GET","POST"])
def edit_lesson(lesson_id):

    if request.method == "POST":

        title = request.form["title"]
        xp = request.form["xp"]
        topic_id = request.form["topic_id"]

        cursor.execute(
        """
        UPDATE lessons
        SET title=?, xp_reward=?
        WHERE id=?
        """,
        (title, xp, lesson_id)
        )

        conn.commit()

        return redirect(request.referrer)

    cursor.execute(
        "SELECT * FROM lessons WHERE id=?",
        (lesson_id,)
    )
    lesson = cursor.fetchone()

    return render_template(
        "edit_lesson.html",
        lesson=lesson
    )

@app.route("/teacher/lesson/<int:lesson_id>")
def teacher_lesson(lesson_id):

    cursor.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
    lesson = cursor.fetchone()

    cursor.execute("SELECT * FROM lesson_contents WHERE lesson_id=?", (lesson_id,))
    contents = cursor.fetchall()

    cursor.execute("SELECT * FROM games WHERE lesson_id=?", (lesson_id,))
    games = cursor.fetchall()

   

    students = []  

    return render_template(
        "teacher_lesson.html",
        lesson=lesson,
        contents=contents,
        games=games,
        students=students
    )

@app.route("/teacher/delete_lesson/<lesson_id>")
def delete_lesson(lesson_id):

    
    cursor.execute(
        "DELETE FROM games WHERE lesson_id=?",
        (lesson_id,)
    )

    
    cursor.execute(
        "DELETE FROM lesson_content WHERE lesson_id=?",
        (lesson_id,)
    )

    
    cursor.execute(
        "DELETE FROM lessons WHERE id=?",
        (lesson_id,)
    )

    conn.commit()

    return redirect(request.referrer)

@app.route("/teacher/delete_topic/<topic_id>")
def delete_topic(topic_id):

    
    cursor.execute(
        "SELECT id FROM lessons WHERE topic_id=?",
        (topic_id,)
    )
    lessons = cursor.fetchall()

    
    for lesson in lessons:
        lesson_id = lesson["id"]

        cursor.execute(
            "DELETE FROM games WHERE lesson_id=?",
            (lesson_id,)
        )

        cursor.execute(
            "DELETE FROM lesson_content WHERE lesson_id=?",
            (lesson_id,)
        )

   
    cursor.execute(
        "DELETE FROM lessons WHERE topic_id=?",
        (topic_id,)
    )

    
    cursor.execute(
        "DELETE FROM topics WHERE id=?",
        (topic_id,)
    )

    conn.commit()

    return redirect(request.referrer)

@app.route("/teacher/game/<game_id>")
def manage_game(game_id):

    cursor.execute("SELECT * FROM games WHERE id=?", (game_id,))
    game = cursor.fetchone()

    cursor.execute("""
    SELECT 
        SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) AS correct,
        SUM(CASE WHEN is_correct=0 THEN 1 ELSE 0 END) AS wrong
    FROM game_results
    WHERE game_id=?
    """, (game_id,))

    stats = cursor.fetchone()

    return render_template(
        "teacher_game_manage.html",
        game=game,
        stats=stats
    )

@app.route("/teacher/delete_game/<game_id>", methods=["POST"])
def delete_game(game_id):

    cursor.execute("DELETE FROM games WHERE id=?", (game_id,))
    conn.commit()

    return redirect(request.referrer)

@app.route("/teacher/edit_game/<game_id>", methods=["GET","POST"])
def edit_game(game_id):

    cursor.execute("SELECT * FROM games WHERE id=?", (game_id,))
    game = cursor.fetchone()
    if not game:
        return "Game không tồn tại"

    import json
    data = json.loads(game.data_json)

    if request.method == "POST":
        import json
        question = request.form["question"]
        new_data = {}

       
        if game.type == "quiz":

            options = request.form.getlist("options[]")
            correct = request.form.get("correct")

            if correct is None:
                correct = 0

            new_data = {
                "options": options,
                "correct": int(correct)
            }

        
        elif game.type == "fill":
            new_data = {
                "answer": request.form["answer"]
            }

        
        elif game.type == "match":
            left = request.form.getlist("left[]")
            right = request.form.getlist("right[]")

            new_data = {
                "pairs": [
                    {"left": l, "right": r}
                    for l, r in zip(left, right)
                ]
            }

        
        elif game.type == "order":
            new_data = {
                "lines": request.form.getlist("lines[]")
            }

        
        elif game.type == "boss":
            new_data = {
                "answer": request.form["answer"]
            }

        cursor.execute("""
            UPDATE games
            SET question=?, data_json=?
            WHERE id=?
        """, (question, json.dumps(new_data), game_id))

        cursor.execute("DELETE FROM game_results WHERE game_id=?", (game_id,))
        conn.commit()

        return redirect("/teacher/lesson/" + str(game.lesson_id))

    return render_template(
        "teacher_edit_game.html",
        game={
            "id": game.id,
            "type": game.type,
            "question": game.question,
            "data": data
        }
    )

from flask import jsonify

from flask import jsonify

@app.route("/check_game", methods=["POST"])
def check_game():

    import json
    from flask import jsonify

    data = request.get_json()
    game_id = data.get("game_id")
    user_answer = data.get("answer")

    cursor.execute("SELECT * FROM games WHERE id=?", (game_id,))
    game = cursor.fetchone()

    if not game:
        return jsonify({"correct": False, "xp": 0})

    game_data = json.loads(game.data_json)

    correct = False
    xp = 0

    
    if game.type == "quiz":

        correct_raw = game_data.get("correct")
        options = game_data.get("options", [])

        
        user_answer = str(user_answer).strip()

       
        correct_str = str(correct_raw).strip()

        
        if user_answer.isdigit():
            user_answer = int(user_answer)

           
            if isinstance(correct_raw, int) or correct_str.isdigit():
                correct = (user_answer == int(correct_raw))
            else:
              
                if options and 0 <= user_answer < len(options):
                    user_answer = options[user_answer]

                correct = str(user_answer).strip() == correct_str

        
        else:
            correct = user_answer == correct_str

        xp = 10 if correct else 0
    
    elif game.type == "fill":

        answer = game_data.get("answer", "")

        if user_answer.strip().lower() == answer.strip().lower():
            correct = True
            xp = 10

    
    elif game.type == "boss":

        answer = game_data.get("answer", "")

        if user_answer.strip().lower() == answer.strip().lower():
            correct = True
            xp = 30

    
    elif game.type == "order":

        try:
            user_order = json.loads(user_answer)
            correct_order = game_data.get("lines", [])

            if user_order == correct_order:
                correct = True
                xp = 15
        except:
            pass

    
    elif game.type == "match":

        try:
            user_map = json.loads(user_answer)

            pairs = game_data.get("pairs", [])

           
            correct_map = {str(i): str(i) for i in range(len(pairs))}

            if user_map == correct_map:
                correct = True
                xp = 15
        except:
            pass

    return jsonify({
        "correct": correct,
        "xp": xp
    })

@app.route("/student/lesson/<int:lesson_id>")
def student_lesson(lesson_id):

    cursor.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
    lesson = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM lesson_contents 
        WHERE lesson_id=?
    """, (lesson_id,))
    contents = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM games 
        WHERE lesson_id=?
    """, (lesson_id,))
    games = cursor.fetchall()

    return render_template(
        "student_lesson.html",
        lesson=lesson,
        contents=contents,
        games=games
    )

@app.route("/teacher/game_stats/<game_id>")
def game_stats(game_id):

    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM game_results
        WHERE game_id=? AND is_correct=1
    """, (game_id,))

    correct_count = cursor.fetchone()[0]

    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM game_results
        WHERE game_id=?
    """, (game_id,))

    total_attempt = cursor.fetchone()[0]

    return render_template(
        "game_stats.html",
        game_id=game_id,
        correct_count=correct_count,
        total_attempt=total_attempt
    )

if __name__ == "__main__":
    app.run(debug=True)
