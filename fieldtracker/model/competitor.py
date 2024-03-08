#!/usr/bin/env python3

from enum import Enum
from .entity import (
    Entity,
    TextFieldSpec,
    IntFieldSpec,
    ForeignFieldSpec,
    EnumTextFieldSpec,
)
from .division import Division


class CompetitorState(Enum):
    VALID = "VALID"
    WITHDRAWN = "WITHDRAWN"
    VETOUT = "VETOUT"


class Competitor(Entity):
    _ENTITY_FIELDS = {
        "div_id": ForeignFieldSpec(Division),
        "cmp_id": IntFieldSpec(minimum=0),
        "cmp_name": TextFieldSpec(),
        "cmp_num": IntFieldSpec(minimum=0),
        "cmp_state": EnumTextFieldSpec(
            CompetitorState, default=CompetitorState.VALID
        ),
    }
    _ENTITY_TABLE = "competitor"
    _ID_FIELD = "cmp_id"
    _UNIQUE = (("div_id", "cmp_num"),)
    _READ_ONLY = ("div_id",)

    def __init__(self, db, div_id, cmp_id, **kwargs):
        super(Competitor, self).__init__(
            db, div_id=div_id, entity_id=cmp_id, **kwargs
        )

    def __str__(self):
        if self["cmp_name"]:
            return "%d. %s" % (self["cmp_num"], self["cmp_name"])
        else:
            return self.uservalue["cmp_num"]
