from holiday_optimizer.problems.base_problem import BaseProblemPage
from holiday_optimizer.problems.minimum_cash_flow.page import MinCashFlowPage

PROBLEMS: list[BaseProblemPage] = [
    MinCashFlowPage(),
]
