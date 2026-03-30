import streamlit as st
import uuid
from datetime import date

from pawpal_system import Owner, Pet, Schedule, Task, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Pets")
if "owner" not in st.session_state or st.session_state.owner is None:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = []

if st.button("Add pet"):
    if st.session_state.owner is None:
        st.session_state.owner = Owner(id=uuid.uuid4(), name=owner_name, email=f"{owner_name.lower()}@example.com")
    new_pet = Pet(id=uuid.uuid4(), name=pet_name, species=species, age=3)
    st.session_state.owner.add_pet(new_pet)
    st.session_state.pets.append(new_pet)

if st.session_state.pets:
    st.write("Current pets:")
    st.write([{"name": p.name, "species": p.species} for p in st.session_state.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    task_data = {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    st.session_state.tasks.append(task_data)
    if st.session_state.pets:
        # assign to first pet for this demo
        assigned_pet = st.session_state.pets[0]
        assigned_task = Task(
            id=uuid.uuid4(),
            title=task_title,
            duration_min=int(duration),
            priority=Priority[priority.upper()],
            type="care",
        )
        assigned_pet.add_task(assigned_task)

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button creates or reuses owner/pet data and runs your scheduler.")

if st.button("Generate schedule"):
    # create or reuse owner/pet
    if st.session_state.owner is None:
        st.session_state.owner = Owner(id=uuid.uuid4(), name=owner_name, email=f"{owner_name.lower()}@example.com")
    if st.session_state.pet is None:
        st.session_state.pet = Pet(id=uuid.uuid4(), name=pet_name, species=species, age=3)
        st.session_state.owner.add_pet(st.session_state.pet)

    # build schedule
    schedule = Schedule(
        id=uuid.uuid4(),
        date=date.today(),
        total_time_available=180,
        owner_id=st.session_state.owner.id,
        pet_id=st.session_state.pet.id,
    )

    for item in st.session_state.tasks:
        pri = Priority[item["priority"].upper()]
        schedule.add_task(
            Task(
                id=uuid.uuid4(),
                title=item["title"],
                duration_min=item["duration_minutes"],
                priority=pri,
                type="care",
            )
        )

    scheduled = schedule.generate_plan()
    st.session_state.owner.set_schedule(schedule)

    st.success("Schedule generated!")
    st.markdown("### Today's Schedule")
    st.text(st.session_state.owner.get_schedule().explain())

    st.markdown("### Task details")
    for t in scheduled:
        st.write(t.info())

