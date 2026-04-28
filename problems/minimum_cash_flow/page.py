import pandas as pd
import streamlit as st

from models.minimum_cash_flow.cash_flow import CashFlowModel, CashFlowResult
from models.minimum_cash_flow.model import min_max_transactions, min_transactions
from models.solver import Solver
from problems.base_problem import BaseProblemPage, ProblemMeta

_OBJECTIVES = {
    "Minimize total transactions": min_transactions,
    "Minimize max transactions per person": min_max_transactions,
}

_SESSION_KEY = "minimum_cash_flow_data"

_DEFAULT_DATA = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie", "Diana"],
    "Balance": [120.0, 40.0, -90, -70],
})


# given the input dataframe (name and balances) and the objective function to uso, it returns a dict with balances and the obj function to use
# in a format suitable for the optimization model
def prepare_model_inputs(df: pd.DataFrame, objective_label: str) -> dict | None:
    df = df.dropna()
    df = df[df["Name"].str.strip() != ""].copy()

    if len(df) < 2:
        st.error("Please enter at least 2 participants.")
        return None

    if df["Name"].duplicated().any():
        st.error("Participant names must be unique.")
        return None

    balances = {row["Name"]: float(row["Balance"]) for _, row in df.iterrows()}

    if(sum(balances.values())) >= 1e-6:
        st.warning("Balances do not sum to zero. Check your input.")
        return None

    return {
        "balances": balances,
        "objective_key": objective_label,
    }


@st.cache_data(show_spinner="Solving...")
def _solve(balances: dict, objective_key: str) -> CashFlowResult | str:
    """Cached solver. Returns CashFlowResult on success or an error string on failure."""
    obj_fn = _OBJECTIVES[objective_key]
    model = CashFlowModel(obj_fn)
    try:
        instance = model.create_instance(dict(balances))
    except ValueError as e:
        return f"Error creating model instance: {e}"
    result = Solver().solve(instance)

    if not result.is_optimal:
        not_opt_message = f"The solver did not find an optimal solution. The status is {result.status.value}."
        if result.error_message:
            not_opt_message += f" Error message: {result.error_message}"
        return not_opt_message

    return model.process_result()


class MinCashFlowPage(BaseProblemPage):

    @property
    def meta(self) -> ProblemMeta:
        return ProblemMeta(
            id="minimum_cash_flow",
            title="Minimum Cash Flow",
            short_description="Settle group holiday expenses with the fewest transactions.",
            icon="💸",
        )

    def render_input(self) -> dict | None:
        st.subheader("Input")

        edited = st.data_editor(
            _DEFAULT_DATA,
            num_rows="dynamic",
            width="stretch",
            key=f"{self.meta.id}_editor",
        )

        objective_label = st.selectbox(
            "Objective",
            options=list(_OBJECTIVES.keys()),
            key=f"{self.meta.id}_objective",
        )

        if st.button("Solve", type="primary", key=f"{self.meta.id}_solve"):
            data = prepare_model_inputs(edited, objective_label)
            if data is not None:
                st.session_state[_SESSION_KEY] = data

        return st.session_state.get(_SESSION_KEY)

    def render_results(self, data: dict) -> None:
        st.subheader("Results")

        balances: dict[str, float] = data["balances"]
        objective_key: str = data["objective_key"]


        result = _solve(balances, objective_key)

        if isinstance(result, str):
            st.error(result)
            return

        cf_result: CashFlowResult = result
        st.success(f"{cf_result.total_transactions} transaction(s) needed")

        st.markdown("### Transactions")
        if cf_result.transactions.empty:
            st.info("No transactions needed — everyone is already settled!")
        else:
            for _, row in cf_result.transactions.iterrows():
                st.markdown(f"**{row['From']}** → **{row['To']}**: €{float(row['Total']):.2f}")

        with st.expander("Transaction matrix"):
            st.dataframe(cf_result.matrix, width="stretch")