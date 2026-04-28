from dataclasses import dataclass
import pandas as pd
import pyomo.environ as pyo
from pyomo.core import floor

from models.base_model import BaseModel
from typing import override


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

    def __init__(self):
        self._abstract_model = self._build()
        self._instance_model = None

    def _build(self) -> pyo.AbstractModel:
        # Data
        model = pyo.AbstractModel()

        model.P = pyo.Set() # persons
        model.balance = pyo.Param(model.P) # balance of each person. Positive -> they should pay that money
                                           # Negative -> they should receive that money

        model.Debitors = pyo.Set(within=model.P, initialize=lambda m : [p for p in m.P if m.balance[p] > 0 ])
        model.Creditors = pyo.Set(within=model.P, initialize=lambda m : [p for p in m.P if m.balance[p] < 0 ])

        # Variables
        model.x = pyo.Var(model.Debitors, model.Creditors, domain=pyo.NonNegativeReals) # how much money debitor p should pay to creditor q
        model.y = pyo.Var(model.Debitors, model.Creditors, domain=pyo.Binary) # whether debitor p should pay to creditor q

        # Objective, minimize the number of transactions
        def objective_rule(model):
            return sum(model.y[p, q] for p in model.Debitors for q in model.Creditors)

        model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # Constraints

        # every person must finish with zero balance
        def debitors_balance_rule(model, debitor):
            return model.balance[debitor] - sum( model.x[debitor, creditor] for creditor in model.Creditors) == 0

        model.DebitorBalanceConstraint = pyo.Constraint(model.Debitors, rule=debitors_balance_rule)

        def creditors_balance_rule(model, creditor):
            return model.balance[creditor] + sum( model.x[debitor, creditor] for debitor in model.Debitors) == 0

        model.CreditorBalanceConstraint = pyo.Constraint(model.Creditors, rule=creditors_balance_rule)

        # relation between x and y. A person should pay another person only if y is 1. And the amount should be less than or equal to the minimum of the balance of the debitor and the creditor (flipped)
        def relation_x_y_rule(model, debitor, creditor):
            M = min(model.balance[debitor], -model.balance[creditor])
            return model.x[debitor, creditor] <= model.y[debitor, creditor] * M

        model.RelationXYConstraint = pyo.Constraint(model.Debitors, model.Creditors, rule=relation_x_y_rule)

        return model

    @override
    def create_instance(self, data : dict) -> pyo.ConcreteModel:
        """
        data = {
            "balances": {
                "Anna": -90, "Carla": -75, ...,
                "Bruno": 82, "Dario": 63, ...
            }
        }
        """
        balances = data['balances']
        _check_balances(balances)
        portal = pyo.DataPortal()

        portal["P"] = list(balances.keys())
        portal["balance"] = dict(balances)

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
