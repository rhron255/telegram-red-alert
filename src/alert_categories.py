from enum import Enum


class AlertCategory(Enum):
    IMPENDING = 14
    OVER = 13
    NOW = 1
    HOSTILE_AIRCRAFT = 2
    # INCOMING_SOON = 10

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.value == other.value
