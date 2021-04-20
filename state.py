from enum import Enum


class WorkerState(Enum):
    Null = -1
    Exploring = 0
    BreadOnly = 1
    GrassOnly = 2
    GoingBase = 3


class SoldierState(Enum):
    Null = -1
    FindingBase = 0
    HelpingWorker = 1
    AttackPreparation = 2
    Defence = 3
