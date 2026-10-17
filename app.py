
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import fitz
import requests
import streamlit as st


# ==================================================
# CONFIGURATION
# ==================================================

APP_DIR = Path(__file__).resolve().parent
DB_FILE = APP_DIR / "student_progress.db"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

MAX_TEXT_LENGTH = 6000
REQUEST_TIMEOUT = 300
QUESTION_COUNT = 5


# ==================================================
# STREAMLIT PAGE
# ==================================================

st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI Learning Assistant")
st.write(
    "Upload your study material, generate summaries and quizzes, "
    "and track your learning progress."
)


# ==================================================
# DATABASE
# ==================================================

def init_db():
    """Create the attempts table and safely migrate old databases."""

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL DEFAULT 'Student',
                topic TEXT NOT NULL DEFAULT 'Study Notes',
                score INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 5,
                created_at TEXT NOT NULL DEFAULT ''
            )
        """)

        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(attempts)"
            ).fetchall()
        }

        required_columns = {
            "student_name": "TEXT NOT NULL DEFAULT 'Student'",
            "topic": "TEXT NOT NULL DEFAULT 'Study Notes'",
            "score": "INTEGER NOT NULL DEFAULT 0",
            "total": "INTEGER NOT NULL DEFAULT 5",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        }

        for column, definition in required_columns.items():
            if column not in columns:
                conn.execute(
                    f"ALTER TABLE attempts "
                    f"ADD COLUMN {column} {definition}"
                )


def save_attempt(name, topic, score, total):
    """Save a completed quiz attempt."""

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO attempts (
                student_name, topic, score, total, created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            topic,
            score,
            total,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))


def get_attempts(name):
    """Retrieve attempts belonging to the current student."""

    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("""
            SELECT topic, score, total, created_at
            FROM attempts
            WHERE student_name = ?
            ORDER BY id DESC
        """, (name,)).fetchall()


init_db()


# ==================================================
# OLLAMA API
# ==================================================

def ask_ollama(prompt, max_tokens=500, json_mode=False):
    """Generate a response from the locally installed Ollama model."""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1 if json_mode else 0.3,
            "num_predict": max_tokens,
            "num_ctx": 4096,
        },
        "keep_alive": "10m",
    }

    if json_mode:
        # Ollama's structured output mode.
        payload["format"] = "json"

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        answer = data.get("response", "").strip()

        if not answer:
            return None, "The AI model returned an empty response."

        return answer, None

    except requests.exceptions.ConnectionError:
        return None, (
            "Cannot connect to Ollama. Open another terminal and run "
            "'ollama run llama3.2:3b'."
        )

    except requests.exceptions.Timeout:
        return None, (
            "The AI model took too long to respond. "
            "Try shorter study material."
        )

    except requests.exceptions.RequestException as error:
        return None, f"Ollama request failed: {error}"


# ==================================================
# PDF TEXT EXTRACTION
# ==================================================

def extract_pdf_text(uploaded_file):
    """Extract text from a text-based PDF."""

    try:
        pdf_bytes = uploaded_file.getvalue()

        with fitz.open(
            stream=pdf_bytes,
            filetype="pdf",
        ) as pdf:
            pages = [
                page.get_text().strip()
                for page in pdf
                if page.get_text().strip()
            ]

        full_text = "\n\n".join(pages).strip()

        if not full_text:
            return None, (
                "No readable text was found in this PDF. "
                "It may be a scanned document; OCR is not included."
            )

        return full_text[:MAX_TEXT_LENGTH], None

    except Exception as error:
        return None, f"Could not read the PDF: {error}"


# ==================================================
# SUMMARY GENERATION
# ==================================================

def generate_summary(text):
    prompt = f"""
You are a college study assistant.

Summarize the following study material for exam revision.

Instructions:
- Use clear, simple English.
- Organize the summary using headings and bullet points.
- Include important definitions, concepts, steps and examples.
- Preserve important technical terminology.
- Do not invent facts that are absent from the material.
- Keep the summary concise and useful for revision.

STUDY MATERIAL:
{text}

Write the summary now.
"""

    return ask_ollama(prompt, max_tokens=450)


# ==================================================
# ROBUST QUIZ GENERATION
# ==================================================

def parse_quiz_response(raw, number_of_questions):
    """Parse and validate JSON returned by Ollama."""

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if isinstance(data, dict):
        # Support either {"questions": [...]} or a single
        # question object returned by the model.
        if isinstance(data.get("questions"), list):
            data = data["questions"]
        elif "question" in data:
            data = [data]
        else:
            return None

    if not isinstance(data, list):
        return None

    valid_questions = []
    seen_questions = set()

    for item in data:
        if not isinstance(item, dict):
            continue

        question = item.get("question")
        options = item.get("options")
        answer = item.get("answer")
        explanation = item.get("explanation", "")

        if not isinstance(question, str) or not question.strip():
            continue

        if not isinstance(options, list) or len(options) != 4:
            continue

        if not all(
            isinstance(option, str) and option.strip()
            for option in options
        ):
            continue

        options = [option.strip() for option in options]

        # All four options must be different.
        if len(set(options)) != 4:
            continue

        if not isinstance(answer, str):
            continue

        answer = answer.strip()

        # The answer must match an option exactly.
        if answer not in options:
            continue

        question_key = question.strip().casefold()

        if question_key in seen_questions:
            continue

        seen_questions.add(question_key)

        valid_questions.append({
            "question": question.strip(),
            "options": options,
            "answer": answer,
            "explanation": (
                explanation.strip()
                if isinstance(explanation, str)
                else ""
            ),
        })

    if len(valid_questions) < number_of_questions:
        return None

    return valid_questions[:number_of_questions]


def generate_quiz(text, number_of_questions=QUESTION_COUNT):
    """Generate MCQs, retrying when Ollama returns invalid output."""

    prompt = f"""
Create exactly {number_of_questions} multiple-choice questions
from the supplied study material.

Return a JSON OBJECT with this exact structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "First possible answer",
        "Second possible answer",
        "Third possible answer",
        "Fourth possible answer"
      ],
      "answer": "Exact text of the correct option",
      "explanation": "Brief explanation of the correct answer"
    }}
  ]
}}

Rules:
1. Include exactly {number_of_questions} questions.
2. Every question must have exactly four distinct options.
3. The answer must exactly match one of those options.
4. Include a short explanation for each answer.
5. Use only information supported by the supplied material.
6. Make questions useful for college exam preparation.
7. Do not add Markdown fences or text outside the JSON object.
8. Escape quotation marks correctly to produce valid JSON.

STUDY MATERIAL:
{text}

Return the completed JSON object.
"""

    # Retry once if the model gives malformed or incomplete output.
    for attempt in range(2):
        raw, error = ask_ollama(
            prompt,
            max_tokens=1600,
            json_mode=True,
        )

        if error:
            return None, error

        questions = parse_quiz_response(
            raw,
            number_of_questions,
        )

        if questions:
            return questions, None

        # On retry, make the required structure more explicit.
        prompt += """
Your previous response was unusable. Return a complete JSON object
with a "questions" array. Every question needs four distinct string
options, an answer matching one option exactly, and an explanation.
Do not return fewer than the requested number of questions.
"""

    return None, (
        "Ollama did not produce a complete, valid quiz after two tries. "
        "Try again, or use a shorter and clearer PDF. "
        "If this keeps happening, the local model may be struggling "
        "with the requested output format."
    )


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "study_text": "",
    "study_topic": "Study Notes",
    "summary": "",
    "quiz": None,
    "quiz_submitted": False,
    "last_saved": False,
    "quiz_score": 0,
    "student_name": "Student",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# SIDEBAR / STUDENT PROFILE
# ==================================================

with st.sidebar:
    st.header("👤 Student Profile")

    name_input = st.text_input(
        "Student name",
        value=st.session_state.student_name,
        key="student_name_input",
    ).strip()

    st.session_state.student_name = name_input or "Student"

    st.divider()
    st.caption(f"AI model: {MODEL_NAME}")
    st.caption("Local inference powered by Ollama.")


# ==================================================
# MAIN TABS
# ==================================================

tab1, tab2, tab3 = st.tabs([
    "📄 Study Material",
    "📝 Quiz",
    "📊 Student Progress",
])


# ==================================================
# TAB 1: STUDY MATERIAL
# ==================================================

with tab1:
    st.subheader("Upload your study material")

    st.write(
        "Upload a text-based PDF to create a summary "
        "or a multiple-choice quiz."
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        key="pdf_uploader",
    )

    if uploaded_file is not None:
        if st.button("📥 Read PDF", key="read_pdf"):
            with st.spinner("Extracting PDF text..."):
                text, error = extract_pdf_text(uploaded_file)

            if error:
                st.error(error)
            else:
                st.session_state.study_text = text
                st.session_state.study_topic = Path(
                    uploaded_file.name
                ).stem

                st.session_state.summary = ""
                st.session_state.quiz = None
                st.session_state.quiz_submitted = False
                st.session_state.last_saved = False

                st.success("PDF loaded successfully.")

    if st.session_state.study_text:
        st.success("Study material is ready.")

        st.write(
            f"**Topic:** {st.session_state.study_topic}"
        )

        with st.expander("Preview extracted text"):
            st.text_area(
                "Extracted PDF text",
                value=st.session_state.study_text,
                height=220,
                disabled=True,
                key="text_preview",
            )

        if st.button(
            "✨ Generate Summary",
            key="generate_summary",
        ):
            with st.spinner(
                "Generating summary. The local model may take a while..."
            ):
                summary, error = generate_summary(
                    st.session_state.study_text
                )

            if error:
                st.error(error)
            else:
                st.session_state.summary = summary

        if st.session_state.summary:
            st.subheader("📘 Study Summary")
            st.markdown(st.session_state.summary)

            st.download_button(
                "⬇️ Download Summary",
                data=st.session_state.summary,
                file_name="study_summary.txt",
                mime="text/plain",
            )

        st.caption(
            "Tip: Shorter PDFs or clearer text can improve local "
            "model speed and response quality."
        )


# ==================================================
# TAB 2: QUIZ
# ==================================================

with tab2:
    st.subheader("Generate and attempt a quiz")

    if not st.session_state.study_text:
        st.info(
            "First open Study Material and load a PDF."
        )

    else:
        st.write(
            f"**Topic:** {st.session_state.study_topic}"
        )

        if st.button(
            f"🧠 Generate {QUESTION_COUNT} MCQs",
            key="generate_quiz",
        ):
            with st.spinner(
                "Generating questions with Ollama. Please wait..."
            ):
                questions, error = generate_quiz(
                    st.session_state.study_text,
                    QUESTION_COUNT,
                )

            if error:
                st.error(error)
            else:
                st.session_state.quiz = questions
                st.session_state.quiz_submitted = False
                st.session_state.last_saved = False
                st.session_state.quiz_score = 0

                # Clear answers from a previous quiz.
                for key in list(st.session_state.keys()):
                    if key.startswith("quiz_answer_"):
                        del st.session_state[key]

                st.success(
                    f"{len(questions)} questions generated successfully."
                )

        questions = st.session_state.quiz

        if questions:
            st.divider()

            with st.form("quiz_form"):
                for index, question in enumerate(questions):
                    st.markdown(
                        f"**Q{index + 1}. {question['question']}**"
                    )

                    st.radio(
                        "Choose one answer:",
                        options=question["options"],
                        index=None,
                        key=f"quiz_answer_{index}",
                    )

                    st.write("")

                submitted = st.form_submit_button(
                    "Submit Quiz",
                    type="primary",
                )

            if submitted:
                score = 0

                for index, question in enumerate(questions):
                    selected = st.session_state.get(
                        f"quiz_answer_{index}"
                    )

                    if selected == question["answer"]:
                        score += 1

                st.session_state.quiz_score = score
                st.session_state.quiz_submitted = True

                if not st.session_state.last_saved:
                    save_attempt(
                        st.session_state.student_name,
                        st.session_state.study_topic,
                        score,
                        len(questions),
                    )
                    st.session_state.last_saved = True

            if st.session_state.quiz_submitted:
                score = st.session_state.quiz_score
                total = len(questions)
                percentage = round(score / total * 100)

                st.divider()
                st.subheader("📊 Your Result")

                col1, col2, col3 = st.columns(3)

                col1.metric("Score", f"{score}/{total}")
                col2.metric("Percentage", f"{percentage}%")
                col3.metric(
                    "Correct Answers",
                    f"{score} of {total}",
                )

                if percentage >= 80:
                    st.success("Excellent work!")
                elif percentage >= 50:
                    st.info("Good effort. Keep practising!")
                else:
                    st.warning(
                        "Review your material and try again."
                    )

                st.subheader("Answer Review")

                for index, question in enumerate(questions):
                    selected = st.session_state.get(
                        f"quiz_answer_{index}"
                    )
                    correct = question["answer"]

                    st.markdown(
                        f"**Q{index + 1}. {question['question']}**"
                    )
                    st.write(
                        f"Your answer: {selected or 'Not answered'}"
                    )
                    st.write(f"Correct answer: {correct}")

                    if question["explanation"]:
                        st.caption(question["explanation"])

                    if selected == correct:
                        st.success("Correct")
                    else:
                        st.error("Incorrect")

                    st.divider()


# ==================================================
# TAB 3: STUDENT PROGRESS
# ==================================================

with tab3:
    st.subheader("📊 Student Progress Tracker")

    attempts = get_attempts(st.session_state.student_name)

    if not attempts:
        st.info(
            "No quiz attempts yet. Complete a quiz to start "
            "tracking your progress."
        )

    else:
        total_attempts = len(attempts)
        total_correct = sum(row[1] for row in attempts)
        total_questions = sum(row[2] for row in attempts)

        average_percentage = (
            round(total_correct / total_questions * 100, 1)
            if total_questions
            else 0
        )

        best_percentage = max(
            (
                round(row[1] / row[2] * 100, 1)
                for row in attempts
                if row[2]
            ),
            default=0,
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Quiz Attempts", total_attempts)
        col2.metric("Average Score", f"{average_percentage}%")
        col3.metric("Best Score", f"{best_percentage}%")

        st.divider()
        st.subheader("Attempt History")

        history = []

        for topic, score, total, created_at in attempts:
            percentage = (
                round(score / total * 100, 1)
                if total
                else 0
            )

            history.append({
                "Date": created_at,
                "Topic": topic,
                "Score": f"{score}/{total}",
                "Percentage": f"{percentage}%",
            })

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True,
        )

        chart_data = [
            {
                "Attempt": f"Attempt {index + 1}",
                "Percentage": (
                    round(row[1] / row[2] * 100, 1)
                    if row[2]
                    else 0
                ),
            }
            for index, row in enumerate(reversed(attempts))
        ]

        st.subheader("Progress Chart")

        st.line_chart(
            chart_data,
            x="Attempt",
            y="Percentage",
        )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "AI Learning Assistant | Python | Streamlit | "
    "Ollama | SQLite"
)
