import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime

# 🔧 Time helpers
def time_to_minutes(t):
    return int(datetime.strptime(t, "%H:%M").hour * 60 + datetime.strptime(t, "%H:%M").minute)

def minutes_to_time(m):
    return f"{m // 60:02d}:{m % 60:02d}"

def define_available_slots(slots):
    return [(time_to_minutes(start), time_to_minutes(end)) for start, end in slots]


# 🧠 Smart Task Scheduler
def schedule_tasks(tasks, available_slots, break_duration=10):
    model = cp_model.CpModel()
    task_vars = {}

    for task in tasks:
        name, duration, priority = task
        start_var = model.NewIntVar(0, 24 * 60, f"start_{name}")
        end_var = model.NewIntVar(0, 24 * 60, f"end_{name}")
        interval = model.NewIntervalVar(start_var, duration, end_var, f"interval_{name}")
        task_vars[name] = (start_var, end_var, interval)

    model.AddNoOverlap([t[2] for t in task_vars.values()])

    all_times = []
    for start, end in available_slots:
        all_times.extend(range(start, end))

    for name, (start_var, end_var, _) in task_vars.items():
        model.AddAllowedAssignments([start_var], [[t] for t in all_times])

    # Enforce breaks between tasks
    task_names = list(task_vars.keys())
    for i in range(len(task_names) - 1):
        current_end = task_vars[task_names[i]][1]
        next_start = task_vars[task_names[i + 1]][0]
        model.Add(next_start >= current_end + break_duration)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        schedule = []
        for name in task_vars:
            start = solver.Value(task_vars[name][0])
            end = solver.Value(task_vars[name][1])
            schedule.append((name, start, end))
        schedule.sort(key=lambda x: x[1])

        final_schedule = []
        for i, (name, start, end) in enumerate(schedule):
            final_schedule.append((name, start, end))
            if i < len(schedule) - 1:
                final_schedule.append(("Break", end, end + break_duration))
        return final_schedule
    else:
        return "❗ Unable to fit all tasks. Try reducing durations or adding more time slots."


# 🌐 Streamlit Web UI
st.set_page_config(page_title="🧠 Smart Day Scheduler", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        padding: 10px 20px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Smart Day Scheduler")
st.markdown("### 👋 Plan your day with AI. Enter your tasks and availability — we'll optimize your schedule!")

with st.expander("📋 How to Use", expanded=False):
    st.markdown("""
    **Step 1:** Add your tasks (name, duration, priority)  
    **Step 2:** Add your available time blocks (e.g., 09:00–12:00)  
    **Step 3:** Choose break duration  
    **Step 4:** Click Generate — we’ll calculate the best schedule! ✅
    """)

# 📌 Tasks
st.subheader("📌 1. Enter Your Tasks")
task_data = st.data_editor(
    {
        "Task Name": ["Emails", "Study", "Workout"],
        "Duration (mins)": [30, 120, 60],
        "Priority (1=High)": [3, 1, 2]
    },
    num_rows="dynamic",
    use_container_width=True,
)

# ⏰ Time Slots
st.subheader("⏰ 2. Set Available Time Slots")
slot_count = st.number_input("How many time slots are you available?", 1, 5, value=2)
slots = []
for i in range(slot_count):
    col1, col2 = st.columns(2)
    with col1:
        start = st.time_input(f"Slot {i+1} start", value=datetime.strptime("09:00", "%H:%M").time(), key=f"start_{i}")
    with col2:
        end = st.time_input(f"Slot {i+1} end", value=datetime.strptime("12:00", "%H:%M").time(), key=f"end_{i}")
    slots.append((start.strftime("%H:%M"), end.strftime("%H:%M")))

# ☕ Break
st.subheader("🧘 3. Choose Break Duration")
break_duration = st.slider("Break Duration Between Tasks (minutes)", 0, 30, 10)

# 🚀 Generate Schedule
st.subheader("🚀 4. Generate Your Optimized Schedule")
if st.button("📅 Generate My Schedule"):
    try:
        tasks = []
        invalid_tasks = []

        for i in range(len(task_data["Task Name"])):
            try:
                name = str(task_data["Task Name"][i]).strip()
                duration = int(task_data["Duration (mins)"][i])
                priority = int(task_data["Priority (1=High)"][i])

                if name and duration > 0:
                    tasks.append((name, duration, priority))
                else:
                    invalid_tasks.append(f"Row {i+1}: Missing or invalid duration/priority")
            except (ValueError, TypeError, KeyError):
                invalid_tasks.append(f"Row {i+1}: Incomplete or invalid task entry")

        if not tasks:
            st.warning("⚠️ No valid tasks entered. Please check your task list.")
            if invalid_tasks:
                with st.expander("🛑 Problems Found in Task Input", expanded=True):
                    for err in invalid_tasks:
                        st.error(err)
        else:
            available_minutes = define_available_slots(slots)
            result = schedule_tasks(tasks, available_minutes, break_duration)

            if isinstance(result, str):
                st.error(result)
            else:
                st.success("✅ Optimized Schedule Created!")
                for name, start, end in result:
                    emoji = "☕" if name == "Break" else "✅"
                    st.write(f"{emoji} **{name}**: {minutes_to_time(start)} – {minutes_to_time(end)}")

                if invalid_tasks:
                    with st.expander("⚠️ Some Tasks Were Skipped", expanded=False):
                        for err in invalid_tasks:
                            st.warning(err)

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
