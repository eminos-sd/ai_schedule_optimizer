import streamlit as st

st.title("AI Schedule Optimizer")

st.header("Add Your Tasks")

tasks = []
task_count = st.number_input("How many tasks?", min_value=1, max_value=20, step=1)

for i in range(task_count):
    with st.expander(f"Task {i+1}"):
        name = st.text_input(f"Task {i+1} name", key=f"name_{i}")
        duration = st.number_input(f"Duration (minutes)", min_value=5, step=5, key=f"duration_{i}")
        priority = st.selectbox(f"Priority", ["High", "Medium", "Low"], key=f"priority_{i}")
        tasks.append({"name": name, "duration": duration, "priority": priority})

st.write("Tasks:", tasks)


from ortools.sat.python import cp_model
from datetime import datetime, timedelta

def schedule_tasks(tasks, total_minutes):
    model = cp_model.CpModel()

    starts = []
    intervals = []
    priority_score = {"High": 3, "Medium": 2, "Low": 1}

    for i, task in enumerate(tasks):
        duration = task["duration"]
        start = model.NewIntVar(0, total_minutes - duration, f"start_{i}")
        end = model.NewIntVar(duration, total_minutes, f"end_{i}")
        interval = model.NewIntervalVar(start, duration, end, f"interval_{i}")

        starts.append(start)
        intervals.append(interval)

    model.AddNoOverlap(intervals)

    model.Maximize(
        sum(priority_score[t["priority"]] * (total_minutes - starts[i])
            for i, t in enumerate(tasks))
    )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result = []
        base_time = datetime.strptime("09:00", "%H:%M")
        for i, task in enumerate(tasks):
            start_min = solver.Value(starts[i])
            start_time = base_time + timedelta(minutes=start_min)
            end_time = start_time + timedelta(minutes=task["duration"])
            result.append({
                "name": task["name"],
                "start": start_time.strftime("%H:%M"),
                "end": end_time.strftime("%H:%M"),
                "priority": task["priority"]
            })
        return sorted(result, key=lambda x: x["start"])
    else:
        return None



st.header("Set Available Time")

total_minutes = st.slider("Total available time (minutes)", 30, 480, 240, step=15)

if st.button("Optimize Schedule"):
    valid_tasks = [t for t in tasks if t["name"] and t["duration"] > 0]
    schedule = schedule_tasks(valid_tasks, total_minutes)

    if schedule:
        st.success("Schedule Created:")
        for t in schedule:
            st.write(f"{t['start']} - {t['end']}: {t['name']} ({t['priority']})")
    else:
        st.error("Could not generate schedule. Try with fewer tasks or longer available time.")
