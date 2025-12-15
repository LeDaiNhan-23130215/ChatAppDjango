from abc import ABC, abstractmethod

class BaseAI(ABC):
    @abstractmethod
    def get_answer(self, question):
        pass