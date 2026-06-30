from holiday_optimizer.problems.base_problem import BaseProblemPage
from holiday_optimizer.problems.minimum_cash_flow.page import MinCashFlowPage
from holiday_optimizer.problems.room_assignment.page import RoomAssignmentPage

PROBLEMS: list[BaseProblemPage] = [
    MinCashFlowPage(),
    RoomAssignmentPage(),
]
