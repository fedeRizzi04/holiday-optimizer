import streamlit as st

from pages.home import render_home
from problems import PROBLEMS

st.set_page_config(
    page_title="Holiday Optimizer",
    page_icon="🏖️",
    layout="wide",
)

problem_pages = [
    st.Page(p.render, title=p.meta.title, icon=p.meta.icon, url_path=p.meta.id)
    for p in PROBLEMS
]

# share page objects with the home page via session state so st.page_link works
st.session_state["_problem_pages"] = problem_pages

nav = st.navigation({
    "": [st.Page(render_home, title="Home", icon="🏠", default=True)],
    "Problems": problem_pages,
})

nav.run()
