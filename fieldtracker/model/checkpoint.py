#!/usr/bin/env python3

from .entity import (
    Entity,
    TextFieldSpec,
    IntFieldSpec,
    ForeignFieldSpec,
)
from .division import Division
from .stage import Stage
from .location import Location


class Checkpoint(Entity):
    _ENTITY_FIELDS = {
        # div and stage referenced here, so we can add a Unique constraint to
        # ensure the check-point number is unique for the division, and the
        # check-point order is unique for the stage.
        "div_id": ForeignFieldSpec(Division),
        "stg_id": ForeignFieldSpec(Stage),
        "loc_id": ForeignFieldSpec(Location),
        "cpt_id": IntFieldSpec(minimum=0),
        "cpt_num": IntFieldSpec(minimum=0),
        "cpt_order": IntFieldSpec(minimum=0),
        # enum not used here, because different event types have different
        # enum values permitted.
        "cpt_type": TextFieldSpec(),
    }
    _ENTITY_TABLE = "checkpoint"
    _ID_FIELD = "cpt_id"
    _UNIQUE = (
        ("div_id", "cpt_num"),
        ("stg_id", "cpt_order"),
    )
    _READ_ONLY = (
        "div_id",
        "stg_id",
    )

    def __init__(self, db, stg_id, cpt_id, **kwargs):
        super(Checkpoint, self).__init__(
            db, stg_id=stg_id, entity_id=cpt_id, **kwargs
        )
