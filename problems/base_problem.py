from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import streamlit as st


@dataclass(frozen=True)
class ProblemMeta:
    id: str
    title: str
    short_description: str
    icon: str


class BaseProblemPage(ABC):

    @property
    @abstractmethod
    def meta(self) -> ProblemMeta:
        pass

    @abstractmethod
    def render_input(self) -> dict | None:
        """Render input widgets. Returns validated input dict when results are ready, None otherwise."""
        pass

    @abstractmethod
    def render_results(self, data: dict) -> None:
        """Render results given the input data dict."""
        pass

    def render(self) -> None:
        st.title(f"{self.meta.icon} {self.meta.title}")

        description_path = Path(__file__).parent / self.meta.id / "description.md"
        if description_path.exists():
            st.markdown(description_path.read_text(encoding="utf-8"))

        st.divider()
        data = self.render_input()
        if data is not None:
            st.divider()
            self.render_results(data)
