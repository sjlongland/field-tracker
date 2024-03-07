#!/usr/bin/env python3

from enum import Enum
from collections import namedtuple
from .entitytype import EntityType


EventEntityName = namedtuple(
    "EventEntityName", ["singular", "plural", "abbr"]
)
EventTypeData = namedtuple(
    "EventTypeData", ["name", "entity_names", "checkpoint_types"]
)


class EventType(Enum):
    """
    Enumeration representing the type of ride event being managed.
    """

    EnduranceRide = "ENDURANCE_RIDE"
    CarRally = "CAR_RALLY"
    BicycleRide = "BICYCLE_RIDE"

    @property
    def data(self):
        return _EVENT_DATA[self]


_DEFAULT_ENTITY_NAMES = {
    EntityType.Division: EventEntityName("Division", "Divisions", "Div"),
    EntityType.Stage: EventEntityName("Stage", "Stages", "Stg"),
    EntityType.Checkpoint: EventEntityName(
        "Checkpoint", "Checkpoints", "Cpt"
    ),
    EntityType.Competitor: EventEntityName(
        "Competitor", "Competitors", "Cmp"
    ),
}


_EVENT_DATA = {
    EventType.EnduranceRide: EventTypeData(
        name="Horse Endurance Ride",
        entity_names=_DEFAULT_ENTITY_NAMES
        | {
            EntityType.Division: EventEntityName("Ride", "Rides", "Rd"),
            EntityType.Stage: EventEntityName("Leg", "Legs", "Lg"),
            EntityType.Checkpoint: EventEntityName(
                "Checkpoint", "Checkpoints", "Cpt"
            ),
            EntityType.Competitor: EventEntityName("Horse", "Horses", "Hrs"),
        },
        checkpoint_types=("Start", "Intermediate", "Strapper", "Finish"),
    ),
    EventType.CarRally: EventTypeData(
        name="Car Rally",
        entity_names=_DEFAULT_ENTITY_NAMES
        | {
            EntityType.Checkpoint: EventEntityName("Car", "Cars", "Car"),
        },
        checkpoint_types=("Start", "Flying Finish"),
    ),
    EventType.BicycleRide: EventTypeData(
        name="Bicycle Ride",
        entity_names=_DEFAULT_ENTITY_NAMES
        | {
            EntityType.Competitor: EventEntityName(
                "Cyclist", "Cyclists", "Cyc"
            ),
        },
        checkpoint_types=("Start", "Intermediate", "Rest Stop", "Finish"),
    ),
}


# Enumerate all the event types, sorted by name for convenience.
EVENT_TYPES = list(EventType)
EVENT_TYPES.sort(key=lambda et: et.data.name)
