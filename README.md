# AI-Learning-Assistant2
# 🎓 AI Learning Assistant

An AI-powered learning application that helps students understand study materials, generate quizzes, evaluate answers, and track their learning progress.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-black?style=for-the-badge)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

## 📌 Project Overview

The **AI Learning Assistant** is a Python-based web application designed to make studying easier and more interactive.

Students can upload PDF study materials, generate AI-powered summaries, create multiple-choice quizzes, receive scores and answer explanations, and monitor their performance over time.

The application uses Streamlit for its user interface, Ollama for local AI inference, PyMuPDF for PDF text extraction, and SQLite to store quiz history.

## ✨ Features

### 📚 1. Study Material Management
- Upload PDF study materials.
- Extract text from uploaded documents.
- Use extracted content as the basis for learning activities.

### 🤖 2. AI-Powered Summarization
- Generate concise summaries of study material.
- Make lengthy notes easier to revise.
- Run the language model locally using Ollama.

### 📝 3. Automatic Quiz Generation
- Generate multiple-choice questions from study content.
- Present questions in an interactive interface.
- Support quiz practice based on uploaded material.

### ✅ 4. Answer Evaluation
- Evaluate submitted quiz answers.
- Calculate quiz scores.
- Display correct answers and explanations.

### 📊 5. Student Progress Tracking
- Save quiz attempts in a local SQLite database.
- Display performance statistics.
- Visualize progress over multiple attempts.

### 🖥️ 6. Interactive Web Interface
- Built with Streamlit.
- Organized into Study Material, Quiz, and Student Progress sections.
- Designed for straightforward use by students.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive web interface |
| Ollama | Running the local language model |
| Llama 3.2 (3B) | Text summarization and quiz generation |
| PyMuPDF | PDF text extraction |
| Requests | Communication with the Ollama API |
| SQLite | Local storage of quiz attempts |
| Git and GitHub | Version control and project hosting |

## 🏗️ System Architecture

```text
        Student
           |
           v
   Streamlit Web App
           |
           v
   Upload Study Material
           |
           v
   PDF Text Extraction
       (PyMuPDF)
           |
           v
    Extracted Text
           |
           v
       Ollama API
           |
           v
     Llama 3.2 (3B)
           |
           v
   +-------+--------+
   |                |
   v                v
Summary         Quiz Generation
                    |
                    v
             Answer Evaluation
                    |
                    v
              Score and Feedback
                    |
                    v
             SQLite Database
                    |
                    v
            Progress Dashboard
```

## 📂 Project Structure

```text
ailearning_assistant/
│
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── readme.md              # Project documentation
├── .gitignore             # Files excluded from Git
└── student_progress.db    # Local database, generated at runtime
```

**Note:** The database is generated locally by the application and should not be uploaded to GitHub.

## ⚙️ Requirements

Before running the project, ensure you have:

- Python installed on your computer.
- Ollama installed and running.
- The `llama3.2:3b` model downloaded.
- Git installed if you want to clone or contribute to the repository.

## 🚀 Installation and Setup

### Step 1: Clone the repository

Replace `YOUR-USERNAME` with your GitHub username.

```bash
git clone https://github.com/YOUR-USERNAME/AI-Learning-Assistant.git
cd AI-Learning-Assistant
```

Alternatively, download the repository as a ZIP file from GitHub.

### Step 2: Install dependencies

```bash
python -m pip install -r requirements.txt
```

If the `python` command is unavailable on Windows, use the full path to your Python executable.

### Step 3: Install Ollama

Download and install Ollama:

https://ollama.com/

### Step 4: Download the AI model

Open a terminal and run:

```bash
ollama pull llama3.2:3b
```

Wait for the download to complete.

### Step 5: Start the application

Make sure Ollama is running, then navigate to the project directory and execute:

```bash
python -m streamlit run app.py
```

If Python is installed at a custom Windows path, run Streamlit using that Python executable.

### Step 6: Open the application

Streamlit will display a local address in the terminal. Open it in your browser:

http://localhost:8501

## 📖 How to Use

1. Launch the application.
2. Open the **Study Material** section.
3. Upload a PDF containing your study notes.
4. Generate and review the summary.
5. Open the **Quiz** section and generate questions.
6. Answer the multiple-choice questions.
7. Review your score, correct answers, and explanations.
8. Open **Student Progress** to review recorded quiz attempts.

The exact options available depend on the current implementation of the application.

## 🗄️ Data Storage

The application uses SQLite to store student quiz attempts locally.

- Database file: `student_progress.db`
- Storage location: The project directory, unless configured otherwise.
- Purpose: Store quiz history and display progress statistics.

The database is local to the computer running the application. It is not automatically shared between users or computers.

## 🔒 Privacy and Security

- The language model is run locally through Ollama.
- Uploaded study material is processed by the application.
- Quiz history is stored in a local database.
- Do not commit API keys, passwords, personal information, or `.env` files to GitHub.
- Review your application and dependencies before using confidential documents.

## 🧪 Testing

To verify the application:

- Confirm that Streamlit starts successfully.
- Upload a readable PDF.
- Check that the summary is generated.
- Generate a quiz and submit answers.
- Confirm that scores and explanations appear.
- Check that quiz attempts appear in Student Progress.

## 🔮 Future Enhancements

Potential improvements include:

- Support for additional document formats.
- Topic-wise quizzes and difficulty settings.
- Flashcard generation.
- Personalized study recommendations.
- Exportable quiz results and progress reports.
- Improved error handling and model response validation.
- Support for additional locally hosted language models.
- Optional deployment for remote access.

## 🎯 Project Objective

The main objective of this project is to demonstrate how artificial intelligence can support personalized learning by combining document processing, automated question generation, answer evaluation, and student progress tracking in one application.

## 👨‍💻 Author

Moniesh yadav

Computer Science and Engineering Student

GitHub:https://github.com/yadavmoniesh-ux

## 📄 License

This project is currently provided without an explicit open-source license. If you want others to reuse and modify your code, consider adding an MIT License file and updating this section accordingly.
