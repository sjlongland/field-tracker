#!/usr/bin/env python3

from enum import Enum

from .entity import (
    Entity,
    IntFieldSpec,
    DateTimeFieldSpec,
    ForeignFieldSpec,
    EnumTextFieldSpec,
)
from .event import Event
from .division import Division
from .checkpoint import Checkpoint
from .competitor import Competitor


class LogStatus(Enum):
    # Partial log entry, needs completion
    Incomplete = "INCOMPLETE"

    # Log entry has invalid data
    Invalid = "INVALID"

    # Log entry is a duplicate
    Duplicate = "DUPLICATE"

    # Newly entered log entry, not yet sent to base
    Logged = "LOGGED"

    # Sent to base
    Sent = "SENT"

    # Base / check-point is querying record
    Inconsistent = "INCONSISTENT"

    # Queried record amended
    Amended = "AMENDED"

    # Obsolete record deleted
    Deleted = "DELETED"


class Log(Entity):
    _ENTITY_FIELDS = {
        "event_id": ForeignFieldSpec(Event),
        "div_id": ForeignFieldSpec(Division, nullable=True),
        "log_id": IntFieldSpec(minimum=0),
        "log_ts": DateTimeFieldSpec(),
        "cpt_num": IntFieldSpec(minimum=0),
        "cpt_id": ForeignFieldSpec(Checkpoint, nullable=True),
        "cmp_num": IntFieldSpec(minimum=0),
        "cmp_id": ForeignFieldSpec(Competitor, nullable=True),
        "log_status": EnumTextFieldSpec(LogStatus, default=LogStatus.Logged),
    }
    _ENTITY_TABLE = "log"
    _ID_FIELD = "log_id"
    _READ_ONLY = ("event_id",)

    def __init__(self, db, event_id, log_id, **kwargs):
        super(Log, self).__init__(
            db, event_id=event_id, entity_id=log_id, **kwargs
        )

    def __str__(self):
        return "OPER:%d %s: CPT %s CMP %s STATUS %s" % (
            self["log_id"],
            self.uservalue["log_ts"],
            self.uservalue["cpt_num"],
            self.uservalue["cmp_num"],
            self.uservalue["log_status"],
        )
