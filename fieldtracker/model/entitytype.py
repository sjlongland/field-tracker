#!/usr/bin/env python3

from enum import Enum


class EntityType(Enum):
    """
    Enumeration representing the type of entities managed.
    """

    Event = "EVENT"
    Division = "DIVISION"
    Stage = "STAGE"
    Checkpoint = "CHECKPOINT"
    Competitor = "Competitor"
