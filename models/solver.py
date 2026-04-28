import pyomo.environ as pyo
import time
from dataclasses import dataclass
from enum import Enum
from pyomo.opt import SolverStatus, TerminationCondition

class ResultStatus(Enum):
    OPTIMAL = 'Optimal'
    INFEASIBLE = 'Infeasible'
    UNBOUNDED = 'Unbounded'
    ERROR = 'Error'

@dataclass
class SolverResult:
    status : ResultStatus
    error_message : str | None
    solve_time : float
    objective : float | None
    instance : pyo.ConcreteModel | None # solved instance model, ready for post processing



def extract_solver_status(result) -> ResultStatus:
    if result.solver.status != SolverStatus.ok:
        return ResultStatus.ERROR

    if result.solver.termination_condition == TerminationCondition.optimal:
        return ResultStatus.OPTIMAL
    if result.solver.termination_condition == TerminationCondition.infeasible:
        return ResultStatus.INFEASIBLE
    if result.solver.termination_condition == TerminationCondition.unbounded:
        return ResultStatus.UNBOUNDED
    return ResultStatus.ERROR

class Solver:
    def __init__(self, solver_name : str = 'gurobi', solver_options : dict = None):
        self._solver = pyo.SolverFactory(solver_name)
        if solver_options:
            for option, value in solver_options.items():
                self._solver.options[option] = value


    def solve(self, instance_model : pyo.ConcreteModel):
        start_time = time.perf_counter()
        try:
            result = self._solver.solve(instance_model)
            solve_time = time.perf_counter() - start_time
        except Exception as e:
            return SolverResult(status=ResultStatus.ERROR, error_message=f"{e}", solve_time=0.0, objective=None, instance=None)

        status = extract_solver_status(result)
        objective = pyo.value(instance_model.obj) if status == ResultStatus.OPTIMAL else None

        return SolverResult(
                status=status,
                error_message=None if status != ResultStatus.ERROR else "An error occurred during solving.",
                solve_time=solve_time,
                objective=objective,
                instance=instance_model if status == ResultStatus.OPTIMAL else None
        )















