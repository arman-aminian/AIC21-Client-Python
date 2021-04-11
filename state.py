from enum import Enum


class WorkerState(Enum):
    Natural = 0
    BreadOnly = 1
    GrassOnly = 2
    GoingBase = 3


class SoldierState(Enum):
    FindingBase = 0
    HelpingWorker = 1
    AttackPreparation = 2
