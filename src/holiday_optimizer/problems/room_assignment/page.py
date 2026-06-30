import pandas as pd
import streamlit as st

from holiday_optimizer.models.room_assignment.room_assignment import (
    RoomAssignmentModel,
    RoomAssignmentResult,
)
from holiday_optimizer.models.solver import Solver
from holiday_optimizer.problems.base_problem import BaseProblemPage, ProblemMeta

_SESSION_KEY = "room_assignment_data"

_DEFAULT_PEOPLE = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
})

_DEFAULT_ROOMS = pd.DataFrame({
    "Room": ["Room 1", "Room 2"],
    "Capacity": [3, 2],
})


def _clean_names(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df:
        return []
    values = df[column].dropna().astype(str).str.strip()
    return [value for value in values if value]


def _preference_table(names: list[str]) -> pd.DataFrame:
    data = []
    for person in names:
        row = {"Person": person}
        for other in names:
            row[other] = 0 if person == other else 1
        data.append(row)
    return pd.DataFrame(data)


def prepare_model_inputs(
    people_df: pd.DataFrame,
    rooms_df: pd.DataFrame,
    preferences_df: pd.DataFrame,
) -> dict | None:
    people = _clean_names(people_df, "Name")
    rooms = _clean_names(rooms_df, "Room")

    if len(people) < 2:
        st.error("Please enter at least 2 people.")
        return None
    if len(set(people)) != len(people):
        st.error("Person names must be unique.")
        return None
    if len(rooms) < 1:
        st.error("Please enter at least 1 room.")
        return None
    if len(set(rooms)) != len(rooms):
        st.error("Room names must be unique.")
        return None

    cleaned_rooms = rooms_df.dropna(subset=["Room"]).copy()
    cleaned_rooms["Room"] = cleaned_rooms["Room"].astype(str).str.strip()
    cleaned_rooms = cleaned_rooms[cleaned_rooms["Room"] != ""]

    try:
        room_capacities = {
            row["Room"]: int(row["Capacity"])
            for _, row in cleaned_rooms.iterrows()
        }
    except (TypeError, ValueError):
        st.error("Room capacities must be whole numbers.")
        return None

    if any(capacity < 1 for capacity in room_capacities.values()):
        st.error("Room capacities must be at least 1.")
        return None
    if sum(room_capacities.values()) < len(people):
        st.error("Total room capacity is not enough for all people.")
        return None

    preferences = {person: {} for person in people}
    indexed_preferences = preferences_df.set_index("Person") if "Person" in preferences_df else pd.DataFrame()
    for person in people:
        for other in people:
            if person == other:
                preferences[person][other] = 0
                continue
            try:
                preferences[person][other] = 1 if int(indexed_preferences.loc[person, other]) == 1 else 0
            except (KeyError, TypeError, ValueError):
                preferences[person][other] = 0

    return {
        "people": people,
        "rooms": room_capacities,
        "preferences": preferences,
    }


@st.cache_data(show_spinner="Solving...")
def _solve(data: dict) -> RoomAssignmentResult | str:
    model = RoomAssignmentModel()
    try:
        instance = model.create_instance(data)
    except ValueError as e:
        return f"Error creating model instance: {e}"

    result = Solver().solve(instance)

    if not result.is_optimal:
        not_opt_message = f"The solver did not find an optimal solution. The status is {result.status.value}."
        if result.error_message:
            not_opt_message += f" Error message: {result.error_message}"
        return not_opt_message

    return model.process_result()


class RoomAssignmentPage(BaseProblemPage):
    @property
    def meta(self) -> ProblemMeta:
        return ProblemMeta(
            id="room_assignment",
            title="Room Assignment",
            short_description="Assign people to rooms while balancing roommate preferences.",
            icon="🛏️",
        )

    def render_input(self) -> dict | None:
        st.subheader("Input")

        people = st.data_editor(
            _DEFAULT_PEOPLE,
            num_rows="dynamic",
            width="stretch",
            key=f"{self.meta.id}_people",
        )

        rooms = st.data_editor(
            _DEFAULT_ROOMS,
            num_rows="dynamic",
            width="stretch",
            key=f"{self.meta.id}_rooms",
        )

        names = _clean_names(people, "Name")
        preferences = st.data_editor(
            _preference_table(names),
            width="stretch",
            disabled=["Person"],
            key=f"{self.meta.id}_preferences",
        )

        if st.button("Solve", type="primary", key=f"{self.meta.id}_solve"):
            data = prepare_model_inputs(people, rooms, preferences)
            if data is not None:
                st.session_state[_SESSION_KEY] = data

        return st.session_state.get(_SESSION_KEY)

    def render_results(self, data: dict) -> None:
        st.subheader("Results")

        result = _solve(data)

        if isinstance(result, str):
            st.error(result)
            return

        assignment_result: RoomAssignmentResult = result
        st.success(f"Minimum happiness: {assignment_result.minimum_happiness:.0f}")

        st.markdown("### Rooms")
        st.dataframe(assignment_result.room_summary, width="stretch", hide_index=True)

        st.markdown("### People")
        st.dataframe(assignment_result.happiness, width="stretch", hide_index=True)
