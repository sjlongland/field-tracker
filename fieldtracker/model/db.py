#!/usr/bin/env python3

"""
Very crude SQLite abstraction for convenient management of database fields.
"""

import sqlite3
import weakref
import logging

from .checkpoint import Checkpoint
from .competitor import Competitor
from .division import Division
from .event import Event
from .location import Location
from .log import Log
from .message import Message
from .stage import Stage


_ALL_ENTITY_TYPES = (
    Checkpoint,
    Competitor,
    Division,
    Event,
    Location,
    Log,
    Message,
    Stage,
)


class Database(object):
    def __init__(self, path, log=None):
        if log is None:
            log = logging.getLogger(self.__class__.__module__)

        self._log = log
        self._conn = sqlite3.connect(path)

        # Create caches
        self._cache = dict(
            (etype._ENTITY_TABLE, weakref.WeakValueDictionary())
            for etype in _ALL_ENTITY_TYPES
        )

    def init(self):
        """
        Initialise a new database
        """
        cur = self._conn.cursor()
        for etype in _ALL_ENTITY_TYPES:
            self._log.debug("Creating table %r", etype._ENTITY_TABLE)
            etype.create(cur)
        self._log.debug("Committed schema")
        self._conn.commit()

    def fetch(self, etype, criteria):
        # Retrieve cache
        cache = self._cache[etype._ENTITY_TABLE]
        log = self._log.getChild(etype._ENTITY_TABLE)

        # Perform the fetch
        for match in self._fetch(etype, criteria):
            entity_id = match[etype._ID_FIELD]
            try:
                # Cached?
                entity = cache[entity_id]
                entity._refresh(match)
                log.debug("Refreshed ID=%r", entity_id)
            except KeyError:
                # Expired from cache
                entity = etype(db, **match)
                cache[entity_id] = entity
                log.debug("Loaded ID=%r", entity_id)

            # Return each match
            yield entity

    def create(self, etype, **fields):
        if etype._ID_FIELD in fields:
            raise ValueError(
                "%r may not be given when creating new entity of type %r"
                % (etype._ID_FIELD, etype._ENTITY_TABLE)
            )

        # Force to None to indicate this is a 'new' row
        fields[etype._ID_FIELD] = None

        return etype(self, **fields)

    def commit(self, statements):
        """
        Commit the changes given by the entity Statements.  This is done in a
        single transaction, or rolled back.
        """
        cur = self._conn.cursor()
        creations = []
        try:
            for statement in statements:
                self._log.debug("Execute: %r", statement)
                cur.execute(statement.statement, statement.arguments)
                if statement.rowid_callback:
                    # Note the statement and row ID
                    creations.append((statement, cur.lastrowid))
        except:
            self._log.debug(
                "Exception occurred during commit %r", statement, exc_info=1
            )
            self._conn.rollback()
            raise

        self._conn.commit()
        self._log.debug("Committed %d statements", len(statements))

        # Pass back committed row IDs
        for statement, row_id in creations:
            try:
                statement.rowid_callback(row_id)
            except:
                self._log.debug(
                    "Failed to notify row ID: statement was %r",
                    statement,
                    exc_info=1,
                )

        # Mark everything committed
        for statement in statements:
            if statement.commit_callback is not None:
                try:
                    statement.commit_callback()
                except:
                    self._log.debug(
                        "Failed to notify commit: statement was %r",
                        statement,
                        exc_info=1,
                    )

    def _fetch(self, etype, criteria):
        (sql, args) = etype.select(criteria)
        self._log.getChild(etype._ENTITY_TABLE).debug(
            "Querying %r (args %r)", sql, args
        )
        cur = self._conn.cursor()
        for row in cur:
            yield etype._decode_row(
                db=self,
                row=dict((c[0], v) for c, v in zip(cur.description, row)),
            )
