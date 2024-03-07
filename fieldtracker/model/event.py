#!/usr/bin/env python3

from .entity import (
    Entity,
    EnumTextFieldSpec,
    TextFieldSpec,
    IntFieldSpec,
    DateFieldSpec,
)
from .eventtype import EventType


class Event(Entity):
    _ENTITY_FIELDS = {
        "event_id": IntFieldSpec(minimum=0),
        "event_type": EnumTextFieldSpec(
            EventType, default=EventType.EnduranceRide
        ),
        "event_name": TextFieldSpec(),
        "auth_org": TextFieldSpec(),
        "location": TextFieldSpec(),
        "start_date": DateFieldSpec(),
        "end_date": DateFieldSpec(),
        "event_tz": TextFieldSpec(),
    }
    _ENTITY_TABLE = "event"
    _ID_FIELD = "event_id"

    def __init__(self, db, event_id, **kwargs):
        super(Event, self).__init__(db, entity_id=event_id, **kwargs)
