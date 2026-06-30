from dataclasses import dataclass
from typing import override

import pandas as pd
import pyomo.environ as pyo

from holiday_optimizer.models.base_model import BaseModel
from holiday_optimizer.models.room_assignment.model import get_room_assignment_model


@dataclass
class RoomAssignmentResult:
    assignments: pd.DataFrame
    room_summary: pd.DataFrame
    happiness: pd.DataFrame
    minimum_happiness: float


def _check_data(data: dict) -> None:
    people = data["people"]
    rooms = data["rooms"]

    if len(people) < 2:
        raise ValueError("Please enter at least 2 people.")
    if len(rooms) < 1:
        raise ValueError("Please enter at least 1 room.")
    if len(set(people)) != len(people):
        raise ValueError("Person names must be unique.")
    if any(capacity < 1 for capacity in rooms.values()):
        raise ValueError("Room capacities must be at least 1.")
    if sum(rooms.values()) < len(people):
        raise ValueError("Total room capacity is not enough for all people.")


class RoomAssignmentModel(BaseModel[RoomAssignmentResult]):
    def __init__(self):
        self._abstract_model = get_room_assignment_model()
        self._instance_model = None

    @override
    def create_instance(self, data: dict) -> pyo.ConcreteModel:
        """
        data =
        {
            "people": ["Alice", "Bob", ...],
            "rooms": {"Room 1": 2, "Room 2": 3, ...},
            "preferences": {
                "Alice": {"Bob": 1, "Charlie": 0, ...},
                ...
            },
        }
        """
        _check_data(data)

        people = list(data["people"])
        rooms = dict(data["rooms"])
        preferences = data["preferences"]

        portal = pyo.DataPortal()
        portal["P"] = people
        portal["C"] = list(rooms.keys())
        portal["cap"] = rooms
        portal["pref"] = {
            (p1, p2): int(preferences.get(p1, {}).get(p2, 0))
            for p1 in people
            for p2 in people
        }

        self._instance_model = self._abstract_model.create_instance(portal)
        return self._instance_model

    @override
    def process_result(self) -> RoomAssignmentResult:
        if self._instance_model is None:
            raise ValueError("Instance model is not created yet. Please call create_instance() first.")

        instance = self._instance_model
        people = list(instance.P)
        rooms = list(instance.C)

        assignment_by_person = {}
        assignment_rows = []
        for person in people:
            assigned_room = next(
                room for room in rooms if pyo.value(instance.x[person, room]) > 0.5
            )
            assignment_by_person[person] = assigned_room
            assignment_rows.append({"Person": person, "Room": assigned_room})

        room_rows = []
        for room in rooms:
            occupants = [
                person
                for person, assigned_room in assignment_by_person.items()
                if assigned_room == room
            ]
            room_rows.append({
                "Room": room,
                "Capacity": int(pyo.value(instance.cap[room])),
                "Occupants": ", ".join(occupants),
                "Used beds": len(occupants),
            })

        happiness_rows = []
        for person in people:
            roommates = [
                other
                for other in people
                if other != person and assignment_by_person[other] == assignment_by_person[person]
            ]
            score = sum(
                1 if int(pyo.value(instance.pref[person, roommate])) == 1 else -1
                for roommate in roommates
            )
            happiness_rows.append({
                "Person": person,
                "Roommates": ", ".join(roommates),
                "Happiness": score,
            })

        return RoomAssignmentResult(
            assignments=pd.DataFrame(assignment_rows),
            room_summary=pd.DataFrame(room_rows),
            happiness=pd.DataFrame(happiness_rows),
            minimum_happiness=float(pyo.value(instance.aux)),
        )
