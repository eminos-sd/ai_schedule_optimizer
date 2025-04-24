# 🧠 AI Schedule Optimizer

An intelligent scheduling assistant that helps you organize your day by auto-assigning tasks to time blocks using optimization logic.

## 🚀 What It Does

- Enter your to-do list (tasks, duration, priority)
- Enter available working time
- Get an optimized schedule instantly using constraint solving (Google OR-Tools)

---

## 🛠 Tech Stack

- 🐍 Python 3.10+
- 🖼 Streamlit (web UI)
- 🔧 OR-Tools (Constraint Programming for task optimization)

---

## 🔧 Setup Instructions

### 1. Clone the Repository


git clone https://github.com/your-username/ai_schedule_optimizer.git
cd ai_schedule_optimizer


### 2. Create and Activate Virtual Environment

python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# OR
venv\Scripts\activate         # Windows

pip install -r requirements.txt

streamlit run app.py 