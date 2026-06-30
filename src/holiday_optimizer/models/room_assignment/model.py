import pyomo.environ as pyo


def get_room_assignment_model() -> pyo.AbstractModel:
    model = pyo.AbstractModel()

    # Data
    model.P = pyo.Set()  # people
    model.C = pyo.Set()  # rooms
    model.cap = pyo.Param(model.C, within=pyo.NonNegativeIntegers)
    model.pref = pyo.Param(model.P, model.P, within=pyo.Binary, default=0)

    model.Pairs = pyo.Set( # pairs of people
        dimen=2,
        initialize=lambda m: [(p1, p2) for p1 in m.P for p2 in m.P if p1 != p2],
    )

    # variables
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary) # if the person p is in the room c
    model.y = pyo.Var(model.Pairs, domain=pyo.Binary) # if the person p1 is in room with the person p2 (need it in the obj function)
    model.aux = pyo.Var(domain=pyo.Reals)

    # Objective: maximize the minimum happiness first, then the total happiness.
    def happiness_expr(model, p1):
        return sum(
            model.y[p1, p2] * (2 * model.pref[p1, p2] - 1)
            for p2 in model.P
            if p1 != p2
        )

    def total_happiness_expr(model):
        return sum(happiness_expr(model, person) for person in model.P)

    def objective_rule(model):
        max_total_happiness_range = 2 * len(model.P) * (len(model.P) - 1) + 1
        return model.aux * max_total_happiness_range + total_happiness_expr(model)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def max_min_rule(model, p1):
        return model.aux <= happiness_expr(model, p1)

    model.MaxMinConstraint = pyo.Constraint(model.P, rule=max_min_rule)

    # Constraints

    def assign_person_room_rule(model, p):
        return sum(model.x[p, c] for c in model.C) == 1

    model.AssignPersonRoomConstraint = pyo.Constraint(model.P, rule=assign_person_room_rule)

    def room_capacity_rule(model, c):
        return sum(model.x[p, c] for p in model.P) <= model.cap[c]

    model.RoomCapacityConstraint = pyo.Constraint(model.C, rule=room_capacity_rule)

    def relation_lower_rule(model, p1, p2, c):
        return model.y[p1, p2] >= model.x[p1, c] + model.x[p2, c] - 1

    model.RelationLowerConstraint = pyo.Constraint(
        model.Pairs,
        model.C,
        rule=relation_lower_rule,
    )

    def relation_upper_rule(model, p1, p2, c):
        return model.y[p1, p2] <= 1 - model.x[p1, c] + model.x[p2, c]

    model.RelationUpperConstraint = pyo.Constraint(
        model.Pairs,
        model.C,
        rule=relation_upper_rule,
    )

    return model
