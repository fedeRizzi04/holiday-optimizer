import pyomo.environ as pyo
from typing import Callable

ObjectiveBuilder = Callable[[pyo.AbstractModel], None]


def min_transactions(model: pyo.AbstractModel):
    def objective_rule(model):
        return sum(model.y[p, q] for p in model.Debitors for q in model.Creditors)
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)


def min_max_transactions(model: pyo.AbstractModel):
    model.minmax = pyo.Var(domain=pyo.NonNegativeIntegers)

    def minmax_rule(model, d):
        return model.minmax >= sum(model.y[d, c] for c in model.Creditors)

    model.MinMaxConstraint = pyo.Constraint(model.Debitors, rule=minmax_rule)

    def objective_rule(model):
        return model.minmax
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)



def get_cash_flow_model(obj : ObjectiveBuilder) -> pyo.AbstractModel:
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

    # Objective, could be either minimizing the number of transactions or minimizing the maximum number of transactions per person
    obj(model)

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
