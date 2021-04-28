from enum import Enum


class WorkerState(Enum):
    Null = -1
    Exploring = 0
    BreadOnly = 1
    GrassOnly = 2
    GoingBase = 3
    Collecting = 4
    InitCollecting = 5
    InitExploring = 6


class SoldierState(Enum):
    Null = -1
    FindingBase = 0
    HelpingWorker = 1
    PreparingForAttack = 2
    Defending = 3
    FirstFewRounds = 4
    CellTargetFound = 5
    HasBeenShot = 6
    AttackingBase = 7
    WaitingForComrades = 8
    BK_GoingNearEnemyBase = 9
    BU_GoingNearEnemyBase = 10
    BK_StayingNearBase = 11
    BU_StayingNearBase = 12
    Explorer_Supporter = 13
