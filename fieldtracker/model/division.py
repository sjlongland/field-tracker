#!/usr/bin/env python3

from .entity import (
    Entity,
    TextFieldSpec,
    IntFieldSpec,
    DateFieldSpec,
    ForeignFieldSpec,
)
from .event import Event


class Division(Entity):
    _ENTITY_FIELDS = {
        "event_id": ForeignFieldSpec(Event),
        "div_id": IntFieldSpec(minimum=0),
        "div_name": TextFieldSpec(),
        "div_num": IntFieldSpec(minimum=0),
        "start_date": DateFieldSpec(),
        "end_date": DateFieldSpec(),
    }
    _ENTITY_TABLE = "division"
    _ID_FIELD = "div_id"
    _UNIQUE = (("event_id", "div_num"),)
    _READ_ONLY = ("event_id",)

    def __init__(self, db, event_id, div_id, **kwargs):
        super(Division, self).__init__(
            db, event_id=event_id, entity_id=div_id, **kwargs
        )

    def __str__(self):
        return "%d. %s" % (self["div_num"], self["div_name"])
