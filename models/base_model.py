from abc import ABC, abstractmethod
import pyomo.environ as pyo

class BaseModel[T](ABC):

    @abstractmethod
    def create_instance(self, data : dict) -> pyo.ConcreteModel:
        pass

    @abstractmethod
    def process_result(self) -> T:
        pass