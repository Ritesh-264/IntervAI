
from flask import (
    Flask, render_template, request,
    redirect, session, url_for, flash
)
import sqlite3
import random
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "intervai_secret_key_change_before_deployment"
DATABASE = "database.db"

# ================= DATABASE =================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS interview_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_count INTEGER NOT NULL,
            partial_count INTEGER NOT NULL,
            incorrect_count INTEGER NOT NULL,
            score INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS interview_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            user_answer TEXT,
            expected_answer TEXT,
            status TEXT NOT NULL,
            score INTEGER NOT NULL,
            feedback TEXT
        )
    """)

    conn.commit()
    conn.close()


# Each category has a question bank.
# Five questions are randomly selected for each interview.

QUESTION_BANK = {
    "technical": [
        {
            "q": "What is a database?",
            "answer": "A database stores and organizes data so it can be accessed and managed.",
            "keywords": ["data", "store", "organize"]
        },
        {
            "q": "What is an API?",
            "answer": "An API allows different software applications to communicate with each other.",
            "keywords": ["applications", "communicate", "software"]
        },
        {
            "q": "What is object-oriented programming?",
            "answer": "OOP organizes code using classes and objects.",
            "keywords": ["class", "object", "code"]
        },
        {
            "q": "What is the difference between frontend and backend?",
            "answer": "Frontend is the user-facing part; backend handles server logic and data.",
            "keywords": ["user", "server", "data"]
        },
        {
            "q": "What is Git used for?",
            "answer": "Git tracks code changes and supports version control.",
            "keywords": ["version", "changes", "code"]
        },
        {
            "q": "What is a primary key in SQL?",
            "answer": "A primary key uniquely identifies each row in a table.",
            "keywords": ["unique", "row", "table"]
        },
        {
            "q": "What is debugging?",
            "answer": "Debugging is finding and fixing errors in a program.",
            "keywords": ["finding", "fixing", "errors"]
        },
        {
            "q": "What is an operating system?",
            "answer": "An operating system manages computer hardware and software resources.",
            "keywords": ["hardware", "software", "resources"]
        }
    ],

    "hr": [
        {
            "q": "Tell me about yourself.",
            "answer": "Introduce your education, technical skills, projects, strengths and career goal.",
            "keywords": ["education", "skills", "project", "goal"]
        },
        {
            "q": "What are your strengths?",
            "answer": "Explain strengths such as problem-solving, teamwork or willingness to learn with examples.",
            "keywords": ["strength", "learn", "example", "teamwork"]
        },
        {
            "q": "Why should we hire you?",
            "answer": "Connect your skills, willingness to learn and relevant projects to the role.",
            "keywords": ["skills", "learn", "project", "role"]
        },
        {
            "q": "Where do you see yourself in five years?",
            "answer": "Describe professional growth, stronger skills and increasing responsibilities.",
            "keywords": ["career", "skills", "growth", "responsibilities"]
        },
        {
            "q": "How do you handle challenges?",
            "answer": "Explain how you identify the problem, plan a solution and learn from results.",
            "keywords": ["problem", "solution", "learn", "plan"]
        },
        {
            "q": "Why do you want this job?",
            "answer": "Connect your interests and skills with the job responsibilities and learning opportunities.",
            "keywords": ["interest", "skills", "job", "learn"]
        },
        {
            "q": "Describe a project you worked on.",
            "answer": "Explain the problem, technologies, your contribution and the result.",
            "keywords": ["problem", "technology", "contribution", "result"]
        },
        {
            "q": "How do you work in a team?",
            "answer": "Describe communication, cooperation, listening and sharing responsibilities.",
            "keywords": ["communication", "cooperation", "team", "responsibilities"]
        }
    ],

    "aptitude": [
        {
            "q": "What is 20% of 250?",
            "answer": "50",
            "keywords": [],
            "objective": True
        },
        {
            "q": "A product costs Rs. 800 and has a 10% discount. What is the final price?",
            "answer": "720",
            "keywords": [],
            "objective": True
        },
        {
            "q": "Find the average of 10, 20 and 30.",
            "answer": "20",
            "keywords": [],
            "objective": True
        },
        {
            "q": "A car travels 120 km in 3 hours. What is its average speed in km/h?",
            "answer": "40",
            "keywords": [],
            "objective": True
        },
        {
            "q": "What is the next number: 2, 4, 6, 8, ?",
            "answer": "10",
            "keywords": [],
            "objective": True
        },
        {
            "q": "If 5 pens cost Rs. 50, what is the cost of one pen?",
            "answer": "10",
            "keywords": [],
            "objective": True
        },
        {
            "q": "What is 15% of 200?",
            "answer": "30",
            "keywords": [],
            "objective": True
        },
        {
            "q": "A number is increased from 100 to 120. What is the percentage increase?",
            "answer": "20%",
            "keywords": [],
            "objective": True
        }
    ],

    "ai": [
        {
            "q": "What is Artificial Intelligence?",
            "answer": "AI enables machines to perform tasks that normally require human intelligence.",
            "keywords": ["machines", "intelligence", "tasks"]
        },
        {
            "q": "What is Generative AI?",
            "answer": "Generative AI creates new content such as text, images, audio or code.",
            "keywords": ["creates", "content", "text", "images"]
        },
        {
            "q": "What is an LLM?",
            "answer": "A large language model is trained on text to understand and generate language.",
            "keywords": ["language", "text", "trained", "generate"]
        },
        {
            "q": "What is prompt engineering?",
            "answer": "Prompt engineering means designing clear instructions to guide an AI model.",
            "keywords": ["instructions", "model", "clear"]
        },
        {
            "q": "What is a chatbot?",
            "answer": "A chatbot is a program that interacts with users through conversation.",
            "keywords": ["program", "users", "conversation"]
        },
        {
            "q": "What is computer vision?",
            "answer": "Computer vision helps computers interpret images and videos.",
            "keywords": ["images", "videos", "interpret"]
        },
        {
            "q": "What is Natural Language Processing?",
            "answer": "NLP enables computers to process and understand human language.",
            "keywords": ["computers", "language", "understand"]
        },
        {
            "q": "What is responsible AI?",
            "answer": "Responsible AI aims for fair, safe, transparent and accountable AI systems.",
            "keywords": ["fair", "safe", "transparent", "accountable"]
        }
    ],

    "python": [
        {
            "q": "What is Python?",
            "answer": "Python is a high-level programming language known for readable syntax.",
            "keywords": ["programming", "language", "syntax"]
        },
        {
            "q": "What is a list in Python?",
            "answer": "A list is an ordered, mutable collection of items.",
            "keywords": ["ordered", "mutable", "items"]
        },
        {
            "q": "What is a dictionary in Python?",
            "answer": "A dictionary stores data as key-value pairs.",
            "keywords": ["key", "value", "pairs"]
        },
        {
            "q": "What is a function?",
            "answer": "A function is a reusable block of code that performs a task.",
            "keywords": ["reusable", "code", "task"]
        },
        {
            "q": "What is the difference between a list and a tuple?",
            "answer": "Lists are mutable, while tuples are immutable.",
            "keywords": ["list", "tuple", "mutable", "immutable"]
        },
        {
            "q": "What is a Python loop?",
            "answer": "A loop repeats a block of code over a sequence or while a condition holds.",
            "keywords": ["repeat", "code", "condition"]
        },
        {
            "q": "What is exception handling?",
            "answer": "Exception handling manages runtime errors using constructs such as try and except.",
            "keywords": ["errors", "try", "except"]
        },
        {
            "q": "What is a Python module?",
            "answer": "A module is a Python file containing reusable code such as functions and variables.",
            "keywords": ["file", "functions", "reusable"]
        }
    ],

    "data-analyst": [
        {
            "q": "What does a data analyst do?",
            "answer": "A data analyst cleans, explores and interprets data to support decisions.",
            "keywords": ["data", "clean", "analyze", "decisions"]
        },
        {
            "q": "What is data cleaning?",
            "answer": "Data cleaning identifies and fixes missing, duplicate or incorrect data.",
            "keywords": ["missing", "duplicate", "incorrect", "data"]
        },
        {
            "q": "What is Pandas used for?",
            "answer": "Pandas is a Python library used to manipulate and analyze structured data.",
            "keywords": ["python", "library", "analyze", "data"]
        },
        {
            "q": "What is data visualization?",
            "answer": "Data visualization presents information using charts and graphs.",
            "keywords": ["charts", "graphs", "information"]
        },
        {
            "q": "What is the difference between WHERE and HAVING in SQL?",
            "answer": "WHERE filters rows before grouping; HAVING filters grouped results.",
            "keywords": ["rows", "grouping", "grouped"]
        },
        {
            "q": "What is a NULL value in SQL?",
            "answer": "NULL represents missing or unknown data in a database.",
            "keywords": ["missing", "unknown", "data"]
        },
        {
            "q": "What is an outlier?",
            "answer": "An outlier is a value that differs substantially from other observations.",
            "keywords": ["value", "differs", "observations"]
        },
        {
            "q": "What is a KPI?",
            "answer": "A key performance indicator measures progress toward a specific objective.",
            "keywords": ["measure", "progress", "objective"]
        }
    ],

    "machine-learning": [
        {
            "q": "What is Machine Learning?",
            "answer": "Machine Learning allows systems to learn patterns from data and make predictions.",
            "keywords": ["learn", "patterns", "data", "predictions"]
        },
        {
            "q": "What is supervised learning?",
            "answer": "Supervised learning trains a model using labeled data.",
            "keywords": ["model", "labeled", "data"]
        },
        {
            "q": "What is unsupervised learning?",
            "answer": "Unsupervised learning finds patterns in data without target labels.",
            "keywords": ["patterns", "data", "labels"]
        },
        {
            "q": "What is overfitting?",
            "answer": "Overfitting occurs when a model learns training data too closely and performs poorly on new data.",
            "keywords": ["training", "model", "new", "data"]
        },
        {
            "q": "Why do we split data into training and testing sets?",
            "answer": "Training data fits the model; testing data evaluates performance on unseen examples.",
            "keywords": ["training", "testing", "performance", "unseen"]
        },
        {
            "q": "What is classification?",
            "answer": "Classification predicts a category or class for an input.",
            "keywords": ["predicts", "category", "class"]
        },
        {
            "q": "What is regression?",
            "answer": "Regression predicts a continuous numerical value.",
            "keywords": ["predicts", "continuous", "numerical"]
        },
        {
            "q": "What is model accuracy?",
            "answer": "Accuracy is the proportion of correct predictions among all predictions.",
            "keywords": ["correct", "predictions", "proportion"]
        }
    ]
}

CATEGORY_NAMES = {
    "technical": "Technical Interview",
    "hr": "HR Interview",
    "aptitude": "Aptitude Test",
    "ai": "AI Interview",
    "python": "Python Interview",
    "data-analyst": "Data Analyst Interview",
    "machine-learning": "Machine Learning Interview"
}


# ================= ANSWER EVALUATION =================

def normalize(text):
    return re.sub(r"[^a-z0-9.% ]", "", text.lower()).strip()


def evaluate_answer(question, answer):
    expected = question["answer"]

    if not answer.strip():
        return "Incorrect", 0, "No answer was provided."

    # Aptitude questions have exact answers.
    if question.get("objective"):
        user_answer = normalize(answer).replace(" ", "")
        correct_answer = normalize(expected).replace(" ", "")

        # Accept 20 or 20.0 for numeric answers, and 20 or 20% for percentage.
        if user_answer == correct_answer:
            return "Correct", 10, "Correct answer."

        try:
            if user_answer.endswith("%") and not correct_answer.endswith("%"):
                user_answer = user_answer[:-1]
            if correct_answer.endswith("%") and not user_answer.endswith("%"):
                correct_answer = correct_answer[:-1]
            if float(user_answer) == float(correct_answer):
                return "Correct", 10, "Correct answer."
        except ValueError:
            pass

        return "Incorrect", 0, "Review the expected answer and try again."

    # Open-ended questions use a simple keyword rubric.
    words = set(re.findall(r"[a-z0-9]+", answer.lower()))
    keywords = question.get("keywords", [])
    matched = sum(1 for keyword in keywords if keyword.lower() in words)
    coverage = matched / max(len(keywords), 1)

    if coverage >= 0.60:
        return "Correct", 10, "Good keyword coverage. Improve clarity and add examples."
    elif coverage >= 0.25:
        return "Partially Correct", 5, "You included some relevant ideas. Add more key points."
    else:
        return "Incorrect", 0, "Your answer may need more relevant details."


# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("This email is already registered. Please log in.", "error")
            return render_template("register.html")
        finally:
            conn.close()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password. Please try again.", "error")

    return render_template("login.html")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access your dashboard.", "error")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session.get("user_name", "User")
    )


# ================= MOCK INTERVIEW =================

@app.route("/mock-interview", methods=["GET", "POST"])
def mock_interview():
    if "user_id" not in session:
        flash("Please log in before starting an interview.", "error")
        return redirect(url_for("login"))

    # Start a new interview when a category is selected or restart is clicked.
    if request.method == "GET" and (
        request.args.get("restart") == "1"
        or "interview_questions" not in session
        or request.args.get("category") in QUESTION_BANK
    ):
        category = request.args.get(
            "category",
            session.get("interview_category", "technical")
        )

        if category not in QUESTION_BANK:
            category = "technical"

        selected = random.sample(
            QUESTION_BANK[category],
            min(5, len(QUESTION_BANK[category]))
        )

        session["interview_category"] = category
        session["interview_questions"] = selected
        session["interview_index"] = 0
        session["interview_answers"] = []

    category = session.get("interview_category", "technical")
    questions = session.get("interview_questions", [])

    if not questions:
        return redirect(url_for("mock_interview", category="technical"))

    index = session.get("interview_index", 0)

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()

        if not answer:
            return render_template(
                "mock_interview.html",
                question=questions[index]["q"],
                current=index + 1,
                total=len(questions),
                category_name=CATEGORY_NAMES[category],
                error="Please enter your answer before continuing."
            )

        question = questions[index]
        status, score, feedback = evaluate_answer(question, answer)

        answers = session.get("interview_answers", [])
        answers.append({
            "question": question["q"],
            "user_answer": answer,
            "expected_answer": question["answer"],
            "status": status,
            "score": score,
            "feedback": feedback
        })
        session["interview_answers"] = answers

        index += 1
        session["interview_index"] = index

        if index >= len(questions):
            correct = sum(a["status"] == "Correct" for a in answers)
            partial = sum(a["status"] == "Partially Correct" for a in answers)
            incorrect = sum(a["status"] == "Incorrect" for a in answers)
            final_score = round(sum(a["score"] for a in answers) / len(answers) * 10)

            conn = get_db_connection()
            cursor = conn.execute("""
                INSERT INTO interview_results
                (user_id, category, completed_at, total_questions,
                 correct_count, partial_count, incorrect_count, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                category,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                len(answers),
                correct,
                partial,
                incorrect,
                final_score
            ))
            result_id = cursor.lastrowid

            for item in answers:
                conn.execute("""
                    INSERT INTO interview_answers
                    (result_id, question, user_answer, expected_answer,
                     status, score, feedback)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result_id,
                    item["question"],
                    item["user_answer"],
                    item["expected_answer"],
                    item["status"],
                    item["score"],
                    item["feedback"]
                ))

            conn.commit()
            conn.close()

            session.pop("interview_questions", None)
            session.pop("interview_index", None)
            session.pop("interview_answers", None)

            return redirect(url_for("interview_result", result_id=result_id))

        return redirect(url_for("mock_interview"))

    return render_template(
        "mock_interview.html",
        question=questions[index]["q"],
        current=index + 1,
        total=len(questions),
        category_name=CATEGORY_NAMES[category],
        error=None
    )


# ================= RESULT =================

@app.route("/interview-result/<int:result_id>")
def interview_result(result_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    result = conn.execute("""
        SELECT * FROM interview_results
        WHERE id = ? AND user_id = ?
    """, (result_id, session["user_id"])).fetchone()

    answers = conn.execute("""
        SELECT * FROM interview_answers
        WHERE result_id = ?
    """, (result_id,)).fetchall()
    conn.close()

    if not result:
        flash("Interview result not found.", "error")
        return redirect(url_for("dashboard"))

    return render_template(
        "result.html",
        result=result,
        answers=answers,
        category_name=CATEGORY_NAMES.get(result["category"], result["category"])
    )


# ================= HISTORY =================

@app.route("/interview-history")
def interview_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    results = conn.execute("""
        SELECT * FROM interview_results
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()
    conn.close()

    return render_template("history.html", results=results, categories=CATEGORY_NAMES)


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ================= START =================

if __name__ == "__main__":
    create_database()
    app.run(debug=True)
