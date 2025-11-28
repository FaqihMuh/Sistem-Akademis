from typing import List, Dict, Any
from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, event_type: str, schedule_data: Dict[str, Any]) -> None:
        pass


class ScheduleSubject:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Attach an observer to the subject"""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from the subject"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_type: str, schedule_data: Dict[str, Any]) -> None:
        """Notify all observers about an event"""
        for observer in self._observers:
            observer.update(event_type, schedule_data)