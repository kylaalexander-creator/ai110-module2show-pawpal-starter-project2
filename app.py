import streamlit as st
import uuid
from datetime import date, time

from pawpal_system import Owner, Pet, Schedule, Task, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session state defaults ────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []      # list of dicts for display
if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None

PRIORITY_COLORS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
TASK_TYPES = ["walk", "feeding", "grooming", "play", "medication", "vet", "cleaning", "care", "other"]

# ── Sidebar — Owner & Pet Setup ───────────────────────────────────────────────
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Pet care scheduling, made simple.")
    st.divider()

    st.subheader("Owner")
    owner_name = st.text_input("Your name", placeholder="e.g. Jordan")
    available_time = st.number_input(
        "Available time today (minutes)", min_value=15, max_value=720, value=180, step=15
    )
    start_time = st.time_input("Day starts at", value=time(8, 0))

    st.divider()
    st.subheader("Add a Pet")
    pet_name = st.text_input("Pet name", placeholder="e.g. Mochi")
    col_sp, col_age = st.columns(2)
    with col_sp:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col_age:
        pet_age = st.number_input("Age (yrs)", min_value=0, max_value=30, value=2)

    if st.button("＋ Add Pet", use_container_width=True):
        if not owner_name.strip():
            st.warning("Enter your name first.")
        elif not pet_name.strip():
            st.warning("Enter a pet name.")
        else:
            if st.session_state.owner is None:
                st.session_state.owner = Owner(
                    id=uuid.uuid4(),
                    name=owner_name.strip(),
                    email=f"{owner_name.strip().lower().replace(' ', '.')}@example.com",
                )
            new_pet = Pet(id=uuid.uuid4(), name=pet_name.strip(), species=species, age=pet_age)
            st.session_state.owner.add_pet(new_pet)
            st.session_state.pets.append(new_pet)
            st.success(f"{pet_name.strip()} added!")

    if st.session_state.pets:
        st.divider()
        st.subheader("Your Pets")
        for p in st.session_state.pets:
            st.markdown(f"**{p.name}** · {p.species}, {p.age} yr{'s' if p.age != 1 else ''}")

    st.divider()
    if st.button("🔄 Reset Everything", use_container_width=True):
        for key in ["owner", "pets", "tasks", "schedule_result"]:
            del st.session_state[key]
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.header("Today's Care Plan")
st.caption(f"Planning for {date.today().strftime('%A, %B %d %Y')}")

tab_tasks, tab_schedule = st.tabs(["📋 Tasks", "📅 Schedule"])

# ── Tab 1: Add & view tasks ───────────────────────────────────────────────────
with tab_tasks:
    st.subheader("Add a Task")

    if not st.session_state.pets:
        st.info("Add at least one pet in the sidebar before creating tasks.")
    else:
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        with c1:
            task_title = st.text_input("Task", placeholder="e.g. Morning walk", label_visibility="collapsed")
        with c2:
            task_type = st.selectbox("Type", TASK_TYPES, label_visibility="collapsed")
        with c3:
            duration = st.number_input("Min", min_value=1, max_value=240, value=20, label_visibility="collapsed")
        with c4:
            priority = st.selectbox("Priority", ["high", "medium", "low"], label_visibility="collapsed")

        pet_names = [p.name for p in st.session_state.pets]
        assigned_pet_name = st.selectbox("Assign to pet", pet_names) if len(pet_names) > 1 else pet_names[0]

        if st.button("＋ Add Task", use_container_width=True):
            if not task_title.strip():
                st.warning("Enter a task name.")
            else:
                new_task = Task(
                    id=uuid.uuid4(),
                    title=task_title.strip(),
                    duration_min=int(duration),
                    priority=Priority[priority.upper()],
                    type=task_type,
                )
                # assign to selected pet
                for p in st.session_state.pets:
                    if p.name == assigned_pet_name:
                        p.add_task(new_task)
                        break
                st.session_state.tasks.append({
                    "Title": task_title.strip(),
                    "Type": task_type,
                    "Duration (min)": int(duration),
                    "Priority": priority.capitalize(),
                    "Pet": assigned_pet_name,
                })
                st.success(f"Task '{task_title.strip()}' added.")

    st.divider()

    if st.session_state.tasks:
        st.subheader(f"Task List ({len(st.session_state.tasks)})")
        for i, t in enumerate(st.session_state.tasks):
            dot = PRIORITY_COLORS.get(t["Priority"].upper(), "⚪")
            st.markdown(
                f"{dot} **{t['Title']}** &nbsp;·&nbsp; {t['Type']} &nbsp;·&nbsp; "
                f"{t['Duration (min)']} min &nbsp;·&nbsp; {t['Pet']}"
            )
    else:
        st.info("No tasks yet. Add one above.")

# ── Tab 2: Generate & view schedule ──────────────────────────────────────────
with tab_schedule:
    st.subheader("Generate Schedule")

    if not st.session_state.pets:
        st.info("Add a pet and some tasks first.")
    elif not st.session_state.tasks:
        st.info("Add at least one task before generating a schedule.")
    else:
        if st.button("▶ Generate Schedule", use_container_width=True, type="primary"):
            owner = st.session_state.owner
            if owner is None:
                owner = Owner(
                    id=uuid.uuid4(),
                    name=owner_name.strip() or "Owner",
                    email="owner@example.com",
                )
                st.session_state.owner = owner

            schedule = Schedule(
                id=uuid.uuid4(),
                date=date.today(),
                total_time_available=available_time,
                owner_id=owner.id,
                pet_id=st.session_state.pets[0].id,
                day_start_hour=start_time.hour,
                day_start_minute=start_time.minute,
            )

            # collect all tasks from all pets
            for p in st.session_state.pets:
                for task in p.tasks:
                    schedule.add_task(task)

            scheduled = schedule.generate_plan()
            sorted_by_time = schedule.sort_tasks_by_time()
            conflicts = schedule.detect_conflicts()
            owner.set_schedule(schedule)

            st.session_state.schedule_result = {
                "scheduled": scheduled,
                "sorted_by_time": sorted_by_time,
                "conflicts": conflicts,
                "available": available_time,
                "used": sum(t.duration_min for t in scheduled),
            }

    result = st.session_state.schedule_result
    if result:
        st.divider()

        # metrics row
        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks Scheduled", len(result["scheduled"]))
        m2.metric("Time Used", f"{result['used']} min")
        m3.metric("Time Remaining", f"{result['available'] - result['used']} min")

        # conflict banner
        if result["conflicts"]:
            st.error(f"⚠️ {len(result['conflicts'])} scheduling conflict(s) detected.")
            for t1, t2 in result["conflicts"]:
                st.write(
                    f"- **{t1.title}** "
                    f"({t1.scheduled_start.strftime('%H:%M')}–{t1.scheduled_end.strftime('%H:%M')}) "
                    f"overlaps with **{t2.title}** "
                    f"({t2.scheduled_start.strftime('%H:%M')}–{t2.scheduled_end.strftime('%H:%M')})"
                )
        else:
            st.success("No conflicts — your day is clear!")

        st.subheader("Schedule")
        if result["sorted_by_time"]:
            for t in result["sorted_by_time"]:
                start = t.scheduled_start.strftime("%H:%M") if t.scheduled_start else "--"
                end = t.scheduled_end.strftime("%H:%M") if t.scheduled_end else "--"
                dot = PRIORITY_COLORS.get(t.priority.name, "⚪")
                st.markdown(
                    f"**{start} – {end}** &nbsp; {dot} {t.title} "
                    f"<span style='color:gray;font-size:0.85em'>{t.type} · {t.duration_min} min</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.warning("No tasks could be scheduled. Check that task durations fit within available time.")
