#!/usr/bin/env python3

"""
Where-clause compiler.
"""


def compile_where(criteria):
    """
    Compile the WHERE clause from the given criteria.

    Criteria given as a dict is taken to be a set of criteria that's ANDed
    together, the keys are fields, the values are the criteria for each field.

    >>> compile_where({"a": ["IN", 1, 2, 3], "b": ["NOT IN", "a", "b", "c"]})
    ('(a IN (?, ?, ?)) AND (b NOT IN (?, ?, ?))', (1, 2, 3, 'a', 'b', 'c'))

    Criteria given as a list is taken to be sets of criteria that are ORed.

    >>> compile_where([{"a": ["IN", 1, 2, 3]}, {"a": ["IN", 4, 5, 6]}])
    ('((a IN (?, ?, ?))) OR ((a IN (?, ?, ?)))', (1, 2, 3, 4, 5, 6))

    Anything else is an error.

    >>> compile_where("this is not a dict or list")
    Traceback (most recent call last):
        ...
    TypeError: Expected a dict or list of criteria items
    """

    if isinstance(criteria, list):
        # OR list of criteria items
        fragments = []
        arguments = []
        for criterion in criteria:
            (sql, args) = compile_where(criterion)
            fragments.append("(%s)" % sql)
            arguments.extend(args)

        return (" OR ".join(fragments), tuple(arguments))
    elif isinstance(criteria, dict):
        # AND mapping of field criteria
        fragments = []
        arguments = []
        for fieldname, fieldcriteria in criteria.items():
            (sql, args) = compile_op(fieldname, fieldcriteria)
            fragments.append("(%s)" % sql)
            arguments.extend(args)

        return (" AND ".join(fragments), tuple(arguments))
    else:
        raise TypeError("Expected a dict or list of criteria items")


def compile_op(field, criteria):
    """
    Compile a single WHERE-clause fragment for a single field.

    >>> compile_op("myfield", ["AND", [">", 10], ["<", 20]])
    ('(myfield > ?) AND (myfield < ?)', (10, 20))
    >>> compile_op("!myfield", ["AND", [">", 10], ["<", 20]])
    ('NOT ((myfield > ?) AND (myfield < ?))', (10, 20))
    """

    if field.startswith("!"):
        negate = True
        field = field[1:]
    else:
        negate = False

    (sql, args) = _compile_op(field, criteria)
    if negate:
        # Negated output
        sql = "NOT (%s)" % sql

    return (sql, args)


def _compile_op(field, criteria):
    """
    Compile a single non-negated WHERE-clause fragment for a single field.
    (inner function)

    >>> _compile_op("myfield", 12345)
    ('myfield = ?', (12345,))
    >>> _compile_op("myfield", ["=", 12345])
    ('myfield = ?', (12345,))
    >>> _compile_op("myfield", ["!=", 12345])
    ('myfield != ?', (12345,))
    >>> _compile_op("myfield", ["AND", [">", 10], ["<", 20]])
    ('(myfield > ?) AND (myfield < ?)', (10, 20))
    >>> _compile_op("myfield", ["OR", [">", 10], ["<", 20]])
    ('(myfield > ?) OR (myfield < ?)', (10, 20))
    >>> _compile_op("myfield", ["OR", ["AND", [">", 10], ["<", 20]], ["AND", [">", 30], ["<", 40]]])
    ('((myfield > ?) AND (myfield < ?)) OR ((myfield > ?) AND (myfield < ?))', (10, 20, 30, 40))
    >>> _compile_op("myfield", ["IN", 1234, 2345])
    ('myfield IN (?, ?)', (1234, 2345))
    >>> _compile_op("myfield", ["NOT IN", 1234, 2345])
    ('myfield NOT IN (?, ?)', (1234, 2345))
    >>> _compile_op("myfield", {})
    Traceback (most recent call last):
        ...
    TypeError: Criteria for 'myfield' must be a list or scalar
    >>> _compile_op("myfield", [])
    Traceback (most recent call last):
        ...
    ValueError: Criteria array requires at least one element
    >>> _compile_op("myfield", ["IN"])
    Traceback (most recent call last):
        ...
    ValueError: 'IN' operator requires at least one argument (got [])
    >>> _compile_op("myfield", ["?"])
    Traceback (most recent call last):
        ...
    ValueError: Unrecognised operator '?' (field 'myfield')
    >>> _compile_op("myfield", ["="])
    Traceback (most recent call last):
        ...
    ValueError: '=' operator requires exactly one argument
    >>> _compile_op("myfield", ["=", 1, 2])
    Traceback (most recent call last):
        ...
    ValueError: '=' operator requires exactly one argument
    """
    if isinstance(criteria, list):
        # Criteria list, first element is the operator
        if len(criteria) == 0:
            raise ValueError("Criteria array requires at least one element")

        op, op_args = (criteria[0], criteria[1:])

        if op in ("AND", "OR"):
            # Inner AND/OR
            fragments = []
            arguments = []

            for op_criteria in op_args:
                (sql, args) = _compile_op(field, op_criteria)
                fragments.append("(%s)" % sql)
                arguments.extend(args)

            return ((" %s " % op).join(fragments), tuple(arguments))
        elif op in ("IN", "NOT IN"):
            if len(op_args) < 1:
                raise ValueError(
                    "%r operator requires at least one argument (got %r)"
                    % (op, op_args)
                )
            # IN or NOT IN operator
            return (
                "%s %s (%s)" % (field, op, ", ".join("?" for n in op_args)),
                tuple(op_args),
            )
        elif op in ("=", "!=", "<", "<=", ">", ">=", "LIKE", "NOT LIKE"):
            # Binary comparison operators
            if len(op_args) != 1:
                raise ValueError(
                    "%r operator requires exactly one argument" % op
                )
            return (
                "%s %s ?"
                % (
                    field,
                    op,
                ),
                (op_args[0],),
            )
        else:
            raise ValueError(
                "Unrecognised operator %r (field %r)" % (op, field)
            )
    elif not isinstance(criteria, dict):
        # Assume equality
        return ("%s = ?" % field, (criteria,))
    else:
        raise TypeError("Criteria for %r must be a list or scalar" % field)
