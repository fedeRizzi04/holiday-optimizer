from dataclasses import dataclass
import pandas as pd
import pyomo.environ as pyo
from pyomo.core import floor
from models.base_model import BaseModel
from typing import override
from models.minimum_cash_flow.model import get_cash_flow_model, ObjectiveBuilder


@dataclass
class CashFlowResult:
    transactions : pd.DataFrame
    matrix : pd.DataFrame
    total_transactions : int


def _check_balances(balances : dict):
    total_balance = sum(balances.values())
    if total_balance != 0:
        raise ValueError(f"The total balance should be zero. Current total balance: {total_balance}")


class CashFlowModel(BaseModel[CashFlowResult]):

    def __init__(self, objective_builder : ObjectiveBuilder):
        self._abstract_model = get_cash_flow_model(objective_builder)
        self._instance_model = None

    @override
    def create_instance(self, data : dict) -> pyo.ConcreteModel:
        """
        data =
        {
            "Anna": -90, "Carla": -75, ...,
            "Bruno": 82, "Dario": 63, ...

        }
        Sum of the balances must be zero. Positive balance means that the person should pay that amount, negative balance means that the person should receive that amount.
        Raises: ValueError if the sum of the balances is not zero.
        """
        _check_balances(data)
        portal = pyo.DataPortal()

        portal["P"] = list(data.keys())
        portal["balance"] = dict(data)

        self._instance_model = self._abstract_model.create_instance(portal)
        return self._instance_model

    @override
    def process_result(self) -> CashFlowResult:
        if self._instance_model is None:
            raise ValueError("Instance model is not created yet. Please call create_instance() first.")

        instance = self._instance_model

        debitors = list(instance.Debitors)
        creditors = list(instance.Creditors)

        data = {}
        rows = []
        for c in creditors:
            data[c] = {}
            for d in debitors:
                value = floor(round(instance.x[d, c].value, 2))
                data[c][d] = value
                if value > 0.001:
                    rows.append({"From": d, "To": c, "Total": value})

        matrix = pd.DataFrame(index=debitors, columns=creditors, data=data)
        matrix.index.name = "Debitors"
        matrix.columns.name = "Creditors"


        return CashFlowResult(transactions = pd.DataFrame(rows), matrix = matrix, total_transactions = len(rows))
