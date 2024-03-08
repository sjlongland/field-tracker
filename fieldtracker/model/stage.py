#!/usr/bin/env python3

from .entity import (
    Entity,
    TextFieldSpec,
    IntFieldSpec,
    ForeignFieldSpec,
)
from .division import Division


class Stage(Entity):
    _ENTITY_FIELDS = {
        "div_id": ForeignFieldSpec(Division),
        "stg_id": IntFieldSpec(minimum=0),
        "stg_name": TextFieldSpec(),
        "stg_num": IntFieldSpec(minimum=0),
        "stg_order": IntFieldSpec(minimum=0),
    }
    _ENTITY_TABLE = "stage"
    _ID_FIELD = "stg_id"
    _UNIQUE = (
        ("div_id", "stg_num"),
        ("div_id", "stg_order"),
    )
    _READ_ONLY = ("div_id",)

    def __init__(self, db, div_id, stg_id, **kwargs):
        super(Stage, self).__init__(
            db, div_id=div_id, entity_id=stg_id, **kwargs
        )

    def __str__(self):
        return "%d. %s" % (self["stg_num"], self["stg_name"])
