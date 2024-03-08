#!/usr/bin/env python3

from collections.abc import MutableMapping
from enum import Enum
import datetime

from .where import compile_where

"""
Very crude SQLite abstraction for convenient management of database fields.
"""


class Entity(MutableMapping):
    @classmethod
    def create(cls, cur):
        colspecs = [
            cls._get_colspec(name, spec)
            for name, spec in cls._ENTITY_FIELDS.items()
        ]

        if isinstance(cls._ENTITY_FIELDS[cls._ID_FIELD], ForeignFieldSpec):
            colspecs.append("PRIMARY KEY (%s)" % cls._ID_FIELD)

        if hasattr(cls, "_UNIQUE"):
            for cols in cls._UNIQUE:
                colspecs.append("UNIQUE (%s)" % (", ".join(cols),))

        statement = "CREATE TABLE IF NOT EXISTS %s (%s)" % (
            cls._ENTITY_TABLE,
            ", ".join(colspecs),
        )

        statement += ";"
        cur.execute(statement)

    @classmethod
    def select(cls, criteria):
        where_sql, where_args = compile_criteria(criteria)
        sql = "SELECT %s FROM %s WHERE %s;" % (
            cls._ENTITY_TABLE,
            ", ".join(sorted(cls._ENTITY_FIELDS.keys())),
            where_sql,
        )
        return (sql, where_args)

    @classmethod
    def _get_colspec(cls, name, spec):
        colspec = "%s %s" % (name, spec.datatype)
        if not spec.nullable:
            colspec += " NOT NULL"

        if isinstance(spec, ForeignFieldSpec):
            colspec += (
                " REFERENCES %s (%s) ON DELETE RESTRICT ON UPDATE RESTRICT"
                % (
                    spec.entity_class._ENTITY_TABLE,
                    spec.field,
                )
            )

        if (name == cls._ID_FIELD) and (spec.datatype == "INTEGER"):
            colspec += " PRIMARY KEY AUTOINCREMENT"

        return colspec

    @classmethod
    def _decode_row(cls, db, row):
        return dict(
            (field, cls._ENTITY_FIELDS[field].from_db(value, db=db))
            for field, value in row.items()
        )

    def __init__(self, db, entity_id, **kwargs):
        self._log = db._log.getChild(
            "%s.%s"
            % (
                self._ENTITY_TABLE,
                entity_id if entity_id is not None else ("@%s" % id(self)),
            )
        )
        self._db = db
        self._entity_id = entity_id
        self._data_fields = {}
        self._changed_fields = {}
        self._db_values = None
        self._user_values = None
        self._delete = False
        self._references = {}

        for name, spec in self._ENTITY_FIELDS.items():
            try:
                value = kwargs[name]
            except KeyError:
                value = spec.default

            if (name == self._ID_FIELD) and (value is None):
                self._log.debug("New entity, not checking ID validity")
                continue

            try:
                spec.check(value)
            except:
                self._log.debug(
                    "Validation error on field %r value %r",
                    name,
                    value,
                    exc_info=1,
                )
                raise

            if name != self._ID_FIELD:
                self._data_fields[name] = value
        self._log.debug(
            "initialised instance with data %r", self._data_fields
        )
        self._link_all()

    def __del__(self):
        self._log.debug("Finalised")

    @property
    def ref(self):
        if self.entity_id is not None:
            return (self._ENTITY_TABLE, self.entity_id, None)
        else:
            return (self._ENTITY_TABLE, None, id(self))

    @property
    def db(self):
        return self._db

    @property
    def entity_id(self):
        return self._entity_id

    @property
    def entity_id_spec(self):
        return self._ENTITY_FIELDS[self._ID_FIELD]

    @property
    def dbvalue(self):
        if self._db_values is None:
            self._db_values = EntityDbValues(self)
        return self._db_values

    @property
    def uservalue(self):
        if self._user_values is None:
            self._user_values = EntityUserValues(self)

        return self._user_values

    @property
    def dirty(self):
        return set(self._changed_fields.keys())

    @property
    def delete(self):
        return self._delete

    @delete.setter
    def delete(self, value):
        self._delete = bool(value)
        self._log.debug("Setting delete flag to %r", self._delete)
        if value:
            self._unlink_all()
        else:
            self._link_all()

    def __repr__(self):
        if self.entity_id is not None:
            return "{%s #%r %r}" % (
                self._ENTITY_TABLE,
                self.entity_id,
                ", ".join("%s=%r" % (k, v) for k, v in self.items()),
            )
        else:
            return "{%s @%r %r}" % (
                self._ENTITY_TABLE,
                id(self),
                ", ".join("%s=%r" % (k, v) for k, v in self.items()),
            )

    def __getitem__(self, name):
        if name == self._ID_FIELD:
            return self.entity_id

        try:
            return self._changed_fields[name]
        except KeyError:
            pass

        return self._data_fields[name]

    def __setitem__(self, name, value):
        if (name == self._ID_FIELD) or (
            hasattr(self, "_READ_ONLY") and (name in self._READ_ONLY)
        ):
            raise ValueError("%s is read-only" % name)

        spec = self._ENTITY_FIELDS[name]
        spec.check(value)
        old = self[name]
        self._changed_fields[name] = value

        if isinstance(spec, ForeignFieldSpec):
            old._unlink(self)
            value._link(self)

    def __delitem__(self, name):
        old = self._changed_fields.pop(name)
        value = self._data_fields[name]

        spec = self._ENTITY_FIELDS[name]
        if isinstance(spec, ForeignFieldSpec):
            old._unlink(self)
            if value is not None:
                value._link(self)

    def __len__(self):
        return len(self._ENTITY_FIELDS)

    def __iter__(self):
        return iter(self._ENTITY_FIELDS.keys())

    def get_references(self, child_class):
        self._log.debug(
            "Looking up references to %r entities (have %s)",
            child_class._ENTITY_TABLE,
            ", ".join(self._references.keys()),
        )
        try:
            references = self._references[child_class._ENTITY_TABLE]
        except KeyError:
            self._log.debug(
                "No references to %r entities found",
                child_class._ENTITY_TABLE,
            )
            return iter([])

        return iter(list(references.values()))

    def revert(self):
        """
        Revert the changes immediately.
        """
        dirty = self.dirty
        for field in dirty:
            del self[field]

    def _set_entity_id(self, row_id):
        if row_id is not None:
            self._entity_id = self.entity_id_spec.from_db(row_id, entity=self)
            self._log = self._db._log.getChild(
                "%s.%s" % (self._ENTITY_TABLE, self._entity_id)
            )
            self._log.debug("Row created")
        else:
            self._entity_id = None
            self._log = self._db._log.getChild(
                "%s.@%s" % (self._ENTITY_TABLE, id(self))
            )
            self._log.debug("Row creation rolled back")

    def _refresh(self, row):
        data = self._decode_row(self._db, row)
        try:
            entity_id = data.pop(self._ID_FIELD)
        except KeyError:
            raise ValueError("No ID field in row")

        if entity_id != this.entity_id:
            raise ValueError("Row does not match this entity's ID")

        self._data_fields.update(data)

    def _link(self, entity):
        self._log.debug("Recording link from %r to %r", entity, self)
        references = self._references.setdefault(entity._ENTITY_TABLE, {})
        references[entity.ref] = entity

    def _link_all(self):
        for name, spec in self._ENTITY_FIELDS.items():
            if isinstance(spec, ForeignFieldSpec):
                self[name]._link(self)

    def _unlink(self, entity):
        self._log.debug("Dropping link from %r to %r", entity, self)
        try:
            references = self._references[entity._ENTITY_TABLE]
        except KeyError:
            return

        try:
            if references[entity.ref] is entity:
                del references[entity.ref]
        except KeyError:
            pass

        if len(references) == 0:
            del self._references[entity._ENTITY_TABLE]

    def _unlink_all(self):
        for name, spec in self._ENTITY_FIELDS.items():
            if isinstance(spec, ForeignFieldSpec):
                self[name]._unlink(self)


class EntityUserValues(MutableMapping):
    def __init__(self, entity):
        self._log = entity._log.getChild("uservalue")
        self._entity = entity

    def __getitem__(self, name):
        ent = self._entity
        value = ent[name]
        spec = ent._ENTITY_FIELDS[name]
        return spec.to_user(value, entity=ent)

    def __setitem__(self, name, value):
        ent = self._entity
        try:
            spec = ent._ENTITY_FIELDS[name]
            native_value = spec.from_user(value, entity=ent)
            ent[name] = native_value
        except:
            self._log.debug("Failed to set %r to %r", name, value, exc_info=1)
            raise

        self._log.debug("Set %r to %r", name, value)

    def __delitem__(self, name):
        del self._entity[name]
        self._log.debug("Cleared %r", name)

    def __len__(self):
        return len(self._entity)

    def __iter__(self):
        return iter(self._entity)


class EntityDbValues(MutableMapping):
    def __init__(self, entity):
        self._log = entity._log.getChild("dbvalue")
        self._entity = entity

    def __getitem__(self, name):
        ent = self._entity
        value = ent[name]
        spec = ent._ENTITY_FIELDS[name]
        return spec.to_db(value, entity=ent)

    def __setitem__(self, name, value):
        ent = self._entity
        try:
            spec = ent._ENTITY_FIELDS[name]
            native_value = spec.from_db(value, entity=ent)
            ent[name] = native_value
        except:
            self._log.debug("Failed to set %r to %r", name, value, exc_info=1)
            raise

        self._log.debug("Set %r to %r", name, value)

    def __delitem__(self, name):
        del self._entity[name]
        self._log.debug("Cleared %r", name)

    def __len__(self):
        return len(self._entity)

    def __iter__(self):
        return iter(self._entity)

    @property
    def statement(self):
        ent = self._entity

        if ent.delete:
            if ent.entity_id is not None:
                return Statement(
                    Action.DELETE,
                    ent._ENTITY_TABLE,
                    where=self.where,
                    commit_callback=self._mark_committed,
                )
            else:
                return None
        elif ent.entity_id is not None:
            dirty = ent.dirty
            changes = dict(
                (name, spec.to_db(ent._changed_fields[name], entity=ent))
                for name, spec in ent._ENTITY_FIELDS.items()
                if name in dirty
            )
            return Statement(
                Action.UPDATE,
                ent._ENTITY_TABLE,
                values=changes,
                where=self.where,
                commit_callback=self._mark_committed,
            )
        else:
            values = dict(
                (name, self[name])
                for name, spec in ent._ENTITY_FIELDS.items()
                if name != ent._ID_FIELD
            )
            return Statement(
                Action.INSERT,
                ent._ENTITY_TABLE,
                values=values,
                rowid_callback=ent._set_entity_id,
                commit_callback=self._mark_committed,
            )

    @property
    def where(self):
        ent = self._entity
        return {
            ent._ID_FIELD: ent.entity_id_spec.to_db(ent.entity_id, entity=ent)
        }

    def commit(self):
        """
        Commit this change immediately
        """
        self._db.commit([self.statement])

    def revert(self):
        self._entity.revert()

    def _mark_committed(self):
        """
        Successful commit callback, amend the current entity data with the
        newly committed changes.
        """
        entity = self._entity
        cache = entity._db._cache[entity._ENTITY_TABLE]
        if entity.delete:
            self._log.debug("Removing deleted entity from cache")
            cache.pop(entity.entity_id, None)
        else:
            self._log.debug("Recording entity as committed")
            entity._data_fields.update(entity._changed_fields)
            entity._changed_fields = {}
            cache[entity.entity_id] = entity


class FieldSpec(object):
    def __init__(self, datatype, default=None, nullable=False, **kwargs):
        self._datatype = datatype
        self._default = default
        self._nullable = nullable

    @property
    def datatype(self):
        return self._datatype

    @property
    def nullable(self):
        return self._nullable

    @property
    def default(self):
        return self._default

    def check(self, value, db=None, entity=None):
        pass

    def from_user(self, value, db=None, entity=None):
        return value

    def to_user(self, value, db=None, entity=None):
        return value

    def from_db(self, value, db=None, entity=None):
        return value

    def to_db(self, value, db=None, entity=None):
        return value


class ForeignFieldSpec(FieldSpec):
    def __init__(self, entity_class, field=None, nullable=None):
        if field is None:
            field = entity_class._ID_FIELD
        spec = entity_class._ENTITY_FIELDS[field]
        super(ForeignFieldSpec, self).__init__(
            datatype=spec.datatype,
            default=spec.default,
            nullable=nullable if nullable is not None else spec.nullable,
        )
        self._entity_class = entity_class
        self._field = field
        self._spec = spec

    @property
    def entity_class(self):
        return self._entity_class

    @property
    def field(self):
        return self._field

    @property
    def spec(self):
        return self._spec

    def check(self, value, db=None, entity=None):
        if not isinstance(value, self.entity_class):
            raise TypeError(
                "expecting %s got %r", self.entity_class.__name__, value
            )

    def from_user(self, value, db=None, entity=None):
        return value

    def to_user(self, value, db=None, entity=None):
        return value

    def from_db(self, value, db=None, entity=None):
        db = db or entity.db
        t_ent_id = self.spec.from_db(value, db=db, entity=entity)
        # Should be only one hit.
        for match in db.fetch(self.entity_class, {self.field: t_ent_id}):
            return match

    def to_db(self, value, db=None, entity=None):
        if value.entity_id is None:
            # We don't know, so return a callable
            def _get_id(display):
                eid = value.entity_id
                if eid is None:
                    if display:
                        return "<placeholder for %s>" % value
                    else:
                        raise ValueError("ID of %r not yet known" % value)

                return self.spec.to_db(eid, db=db, entity=entity)

            return _get_id
        else:
            # ID value known now, so use that
            return self.spec.to_db(value.entity_id, db=db, entity=entity)


class RangeFieldSpec(FieldSpec):
    def __init__(self, datatype, minimum=None, maximum=None, **kwargs):
        super(RangeFieldSpec, self).__init__(datatype, **kwargs)
        self._minimum = minimum
        self._maximum = maximum

    def check(self, value, db=None, entity=None):
        if (self._minimum is not None) and (value < self._minimum):
            raise ValueError("%s value too low" % value)

        if (self._maximum is not None) and (value > self._maximum):
            raise ValueError("%s value too high" % value)


class TextFieldSpec(FieldSpec):
    def __init__(self, **kwargs):
        super(TextFieldSpec, self).__init__("TEXT", **kwargs)

    def from_user(self, value, db=None, entity=None):
        return value or None

    def to_user(self, value, db=None, entity=None):
        return value or ""


class EnumTextFieldSpec(TextFieldSpec):
    def __init__(self, enum_class, **kwargs):
        super(TextFieldSpec, self).__init__("TEXT", **kwargs)
        self._enum_class = enum_class

    def check(self, value, db=None, entity=None):
        self._enum_class(value)

    def from_user(self, value, db=None, entity=None):
        return self._enum_class(value)

    def to_user(self, value, db=None, entity=None):
        return value.name

    def from_db(self, value, db=None, entity=None):
        return self._enum_class(value)

    def to_db(self, value, db=None, entity=None):
        return value.value


class IntFieldSpec(RangeFieldSpec):
    def __init__(self, **kwargs):
        super(IntFieldSpec, self).__init__("INTEGER", **kwargs)

    def from_user(self, raw, db=None, entity=None):
        return int(raw, base=10)

    def to_user(self, value, db=None, entity=None):
        return str(value)


class EnumIntFieldSpec(TextFieldSpec):
    def __init__(self, enum_class, **kwargs):
        super(TextFieldSpec, self).__init__("INTEGER", **kwargs)
        self._enum_class = enum_class

    def check(self, value, db=None, entity=None):
        self._enum_class(value)

    def from_user(self, value, db=None, entity=None):
        return self._enum_class(value)

    def to_user(self, value, db=None, entity=None):
        return value.name

    def from_db(self, value, db=None, entity=None):
        return self._enum_class(value)

    def to_db(self, value, db=None, entity=None):
        return value.value


class DateFieldSpec(RangeFieldSpec):
    def __init__(self, **kwargs):
        super(DateFieldSpec, self).__init__("TEXT", **kwargs)

    def from_user(self, raw, db=None, entity=None):
        return datetime.date.fromisoformat(raw)

    def to_user(self, value, db=None, entity=None):
        return value.isoformat()

    def from_db(self, raw, db=None, entity=None):
        return self.from_user(raw, db=db, entity=entity)

    def to_db(self, value, db=None, entity=None):
        return self.to_user(value, db=db, entity=entity)


class DateTimeFieldSpec(RangeFieldSpec):
    def __init__(self, **kwargs):
        super(DateTimeFieldSpec, self).__init__("INTEGER", **kwargs)

    def from_user(self, raw, db=None, entity=None):
        return datetime.date.fromisoformat(raw)

    def to_user(self, db, entity, value):
        return value.isoformat()

    def from_db(self, db, entity, raw):
        return datetime.datetime.fromtimestamp(raw, tz=datetime.timezone.utc)

    def to_db(self, db, entity, value):
        return int(value.timestamp())


class Action(Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class Statement(object):
    def __init__(
        self,
        action,
        table,
        values=None,
        criteria=None,
        commit_callback=None,
        rowid_callback=None,
    ):
        if values is not None:
            if action in (Action.DELETE,):
                raise ValueError(
                    "values must be None for action=%s" % action.name
                )
            (v_fields, v_values) = zip(*values.items())

        if criteria is not None:
            if action in (Action.INSERT,):
                raise ValueError(
                    "criteria must be None for action=%s" % action.name
                )
            (c_fields, c_values) = zip(*criteria.items())
        elif action in (Action.UPDATE, Action.DELETE):
            raise ValueError(
                "criteria must NOT be None for action=%s" % action.name
            )

        if action == Action.INSERT:
            self._statement = "INSERT INTO %s (%s) VALUES (%s)" % (
                table,
                ", ".join(v_fields),
                ", ".join("?" for f in v_fields),
            )
            self._arguments = tuple(v_values)

            if criteria is not None:
                raise ValueError("INSERT with WHERE not possible")
        elif action == Action.UPDATE:
            self._statement = "UPDATE %s SET %s" % (
                table,
                ", ".join("%s = ?" % f for f in v_fields),
            )
            self._arguments = tuple(v_values)
        elif action == Action.DELETE:
            self._statement = "DELETE FROM %s" % table
            self._arguments = ()

        if criteria is not None:
            (w_sql, w_args) = compile_where(criteria)
            self._statement += " WHERE %s;" % w_sql
            self._arguments += w_args
        else:
            self._statement += ";"

        self._rowid_callback = rowid_callback
        self._commit_callback = commit_callback

    @property
    def statement(self):
        return self._statement

    @property
    def arguments(self):
        return self._get_arguments(display=False)

    @property
    def rowid_callback(self):
        return self._rowid_callback

    @property
    def commit_callback(self):
        return self._commit_callback

    def __repr__(self):
        return "%s{%s :: %r}" % (
            self.__class__.__name__,
            self.statement,
            self._get_arguments(True),
        )

    def _get_arguments(self, display=False):
        return tuple(self._get_value(arg, display) for arg in self._arguments)

    def _get_value(self, arg, display):
        if callable(arg):
            # Call the function to determine the value to insert
            return arg(display)
        else:
            # Return the argument as-is
            return arg
