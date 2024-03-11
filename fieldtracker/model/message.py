#!/usr/bin/env python3

from enum import Enum

from .entity import (
    Entity,
    TextFieldSpec,
    IntFieldSpec,
    DateTimeFieldSpec,
    ForeignFieldSpec,
    EnumIntFieldSpec,
    EnumTextFieldSpec,
)
from .event import Event
from .division import Division
from .stage import Stage
from .checkpoint import Checkpoint
from .competitor import Competitor


class MessageSeverity(Enum):
    Emergency = 0
    Alert = 1
    Critical = 2
    Error = 3
    Warning = 4
    Notice = 5
    Info = 6
    Debug = 7


class MessageStatus(Enum):
    Recorded = "RECORDED"
    Acknowledged = "ACKNOWLEDGED"
    Actioned = "ACTIONED"


class Message(Entity):
    _ENTITY_FIELDS = {
        "event_id": ForeignFieldSpec(Event),
        "msg_id": IntFieldSpec(minimum=0),
        "msg_ts": DateTimeFieldSpec(),
        "msg_div_id": ForeignFieldSpec(Division, nullable=True),
        "msg_stg_id": ForeignFieldSpec(Stage, nullable=True),
        "msg_cpt_id": ForeignFieldSpec(Checkpoint, nullable=True),
        "msg_cmp_id": ForeignFieldSpec(Competitor, nullable=True),
        "msg_severity": EnumIntFieldSpec(
            MessageSeverity, default=MessageSeverity.Info
        ),
        "msg_status": EnumTextFieldSpec(
            MessageStatus, default=MessageStatus.Recorded
        ),
        "msg_text": TextFieldSpec(),
    }
    _ENTITY_TABLE = "message"
    _ID_FIELD = "msg_id"
    _READ_ONLY = ("event_id",)

    def __init__(self, db, event_id, msg_id, **kwargs):
        super(Message, self).__init__(
            db, event_id=event_id, entity_id=msg_id, **kwargs
        )

    def __str__(self):
        return "MSG:%d %s: %s" % (
            self["msg_id"],
            self.uservalue["msg_ts"],
            self.uservalue["msg_text"],
        )
