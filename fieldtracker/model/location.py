#!/usr/bin/env python3

from .entity import (
    Entity,
    TextFieldSpec,
    IntFieldSpec,
    ForeignFieldSpec,
)
from .event import Event


class Location(Entity):
    _ENTITY_FIELDS = {
        "event_id": ForeignFieldSpec(Event),
        "loc_id": IntFieldSpec(minimum=0),
        "loc_name": TextFieldSpec(),
        "loc_num": IntFieldSpec(minimum=0),
        "loc_tz": TextFieldSpec(nullable=True),
    }
    _ENTITY_TABLE = "location"
    _ID_FIELD = "loc_id"
    _UNIQUE = (
        ("event_id", "loc_name"),
        ("event_id", "loc_num"),
    )
    _READ_ONLY = ("event_id",)

    def __init__(self, db, event_id, loc_id, **kwargs):
        super(Location, self).__init__(
            db, event_id=event_id, entity_id=loc_id, **kwargs
        )
