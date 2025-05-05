import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime, timedelta


# 🔧 Utility functions
def time_to_minutes(t):
    return int(datetime.strptime(t, "%H:%M").hour * 60 + datetime.strptime(t, "%H:%M").minute)


def minutes_to_time(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def define_available_slots(slots):
    return [(time_to_minutes(start), time_to_minutes(end)) for start, end in slots]


# 🧠 Scheduling Logic
def schedule_tasks(tasks, available_slots, break_duration=10):
    model = cp_model.CpModel()
    task_vars = {}

    # Generate task intervals
    for task in tasks:
        name, duration, priority = task
        start_var = model.NewIntVar(0, 24 * 60, f"start_{name}")
        end_var = model.NewIntVar(0, 24 * 60, f"end_{name}")
        interval = model.NewIntervalVar(start_var, duration, end_var, f"interval_{name}")
        task_vars[name] = (start_var, end_var, interval)

    # No overlap
    model.AddNoOverlap([t[2] for t in task_vars.values()])

    # Time windows constraint
    all_times = []
    for start, end in available_slots:
        all_times.extend(range(start, end))
    for name, (start_var, end_var, _) in task_vars.items():
        model.AddAllowedAssignments([start_var], [[t] for t in all_times])

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        schedule = []
        for name in task_vars:
            start = solver.Value(task_vars[name][0])
            end = solver.Value(task_vars[name][1])
            schedule.append((name, start, end))
        # Sort by start time
        schedule.sort(key=lambda x: x[1])

        # Insert breaks
        final_schedule = []
        for i, (name, start, end) in enumerate(schedule):
            final_schedule.append((name, start, end))
            if i < len(schedule) - 1:
                next_start = schedule[i + 1][1]
                if next_start - end >= break_duration:
                    final_schedule.append(("Break", end, end + break_duration))

        return final_schedule
    else:
        unscheduled_tasks = [task[0] for task in tasks]
        return f"❗ Unable to fit all tasks. Try reducing durations or extending available time.\nTasks: {unscheduled_tasks}"


# 🖼 Streamlit UI
st.set_page_config(page_title="🧠 Smart Day Scheduler", layout="centered")
st.title("🧠 Intelligent Scheduling Assistant")

st.markdown("Enter your **tasks**, your **available time slots**, and get an optimized schedule!")

# 🎯 Enter tasks
st.header("1️⃣ Tasks")
task_data = st.data_editor(
    {
        "Task Name": ["Emails", "Study", "Workout"],
        "Duration (mins)": [30, 120, 60],
        "Priority (1=High)": [3, 1, 2]
    },
    num_rows="dynamic",
    use_container_width=True,
)


# ⏰ Time slots
st.header("2️⃣ Available Time Slots")
slot_count = st.number_input("How many time slots are you available?", 1, 5, value=2)
slots = []
for i in range(slot_count):
    col1, col2 = st.columns(2)
    with col1:
        start = st.time_input(f"Slot {i+1} start", value=datetime.strptime("09:00", "%H:%M").time(), key=f"start_{i}")
    with col2:
        end = st.time_input(f"Slot {i+1} end", value=datetime.strptime("12:00", "%H:%M").time(), key=f"end_{i}")
    slots.append((start.strftime("%H:%M"), end.strftime("%H:%M")))

# 🧘 Break duration
break_duration = st.slider("Break Duration Between Tasks (minutes)", 0, 30, 10)

# 🔘 Button
if st.button("📅 Generate My Schedule"):
    try:
        tasks = []
        for i in range(len(task_data["Task Name"])):
            name = task_data["Task Name"][i]
            duration = int(task_data["Duration (mins)"][i])
            priority = int(task_data["Priority (1=High)"][i])
            if name.strip():
                tasks.append((name, duration, priority))

        available_minutes = define_available_slots(slots)

        result = schedule_tasks(tasks, available_minutes, break_duration)

        if isinstance(result, str):
            st.error(result)
        else:
            st.success("✅ Optimized Schedule Created!")
            for name, start, end in result:
                emoji = "☕" if name == "Break" else "✅"
                st.write(f"{emoji} **{name}**: {minutes_to_time(start)} – {minutes_to_time(end)}")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
