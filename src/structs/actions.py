from enum import Enum


class DemingAction(Enum):
    """Set of actions that the system can perform, based on the Deming Cylce (PDCA)"""

    PLAN = "plan"
    DO = "do"
    CHECK = "check"
    ACT = "act"
