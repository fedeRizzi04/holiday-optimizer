import streamlit as st

from holiday_optimizer.problems import PROBLEMS


def render_home() -> None:
    st.title("🏖️ Holiday Optimizer")
    st.markdown(
        "A collection of optimization problems to make your holidays smoother. "
        "Pick a problem below and solve your own instance!"
    )
    st.divider()

    st.subheader("Problems")
    problem_pages: list[st.Page] = st.session_state.get("_problem_pages", [])

    cols = st.columns(min(len(PROBLEMS), 3), gap="medium")
    for i, (problem, page) in enumerate(zip(PROBLEMS, problem_pages)):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {problem.meta.icon} {problem.meta.title}")
                st.write(problem.meta.short_description)
                st.page_link(page, label="Open →", width="stretch")
