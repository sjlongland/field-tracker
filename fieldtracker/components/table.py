#!/usr/bin/env python3

"""
Simplified table widget based on ttk.Treeview.  This simplifies the Treeview
widget, distilling the essential functions needed to manage a simple table
view.

The Treeview widget is actually very capable, but it has a rather obscure API
owing to its complexity _and_ its background as being a Tk widget that has
been "mapped" to Python's API.

The following wrapper provides a simplified and opinionated interface that
allows for display and manipulation of tabular data only.  A distinctly "KISS"
approach is taken here.

- multi-selections are supported, but not the default
- true 'tree' structures are not supported
- `None` is rendered as an empty string
- Other data types are coerced to strings on passing to the Treeview
- There is some support there for custom row types through subclassing
"""

# © 2024 Stuart Longland VK4MSL
# SPDX-License-Identifier: Python-2.0

from collections.abc import MutableSequence, MutableMapping, Sequence, Mapping

# GUI stuff
import tkinter
from tkinter import ttk


class TableItem(MutableMapping):
    """
    Item base class for representing rows in the table.  This stores
    references to the textual label for the row (left-most column), any values
    for the columns themselves, the item ID (as assigned by Tkinter) and a
    reference to an application-specific object.

    :param table:       The Table object that this row is a part of.
    :type table:        class:`Table`
    :param value:       The value representing the label of the row.  If not a
                        string, it will be stringified using the ``str()``
                        operator.
    :param columns:     The values of the optional data columns.
    :type columns:      tuple
    :param iid:         The iid returned by ``tkinter`` when inserted
    :type iid:          str
    :param objectref:   Optional object reference for the application
    """

    def __init__(self, table, value, columns=None, iid=None, objectref=None):
        self._table = table
        self._value = value
        self._columns = list(columns)
        self._iid = iid
        self._objectref = objectref

    # Debugging

    def __repr__(self):
        return "%s(table=%r, value=%r, columns=%r, iid=%r, objectref=%r)" % (
            self.__class__.__name__,
            self._table,
            self._value,
            self._columns,
            self._iid,
            self._objectref,
        )

    # Interaction with the item label itself

    @property
    def value(self):
        """
        Return the value associated for this row.
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Update the value associated with this row.
        """
        self._value = value

        if self._iid is not None:
            # Stringify "value" in case it's an object
            self._table._treeview.item(self._iid, text=self._get_text(value))

    @property
    def objectref(self):
        """
        Return the application object linked to this row.
        """
        return self._objectref

    @objectref.setter
    def objectref(self, value):
        """
        Update the application object linked to this row.
        """
        self._objectref = value

    # MutableMapping interface for interacting with columns

    def __getitem__(self, key):
        """
        Return the value of the column specified by ``key``.

        :param key: Either the name or index of the column requested.
        :type key: str or int
        """
        (pos,) = self._get_pos(key)
        return self._columns[pos]

    def __setitem__(self, key, value):
        """
        Set the value of the column specified by ``key``.

        :param key:     Either the name or index of the column requested.
        :type key:      str or int
        :param value:   The value being set, if it is not a ``str``, it will
                        be stringified before being passed to the Treeview.
        """
        (pos, name) = self._get_pos(key)
        self._set_column(name, pos, value)

    def __delitem__(self, key):
        """
        Clear the value of the column specified by ``key``.  This is
        equivalent to:

        item[key] = None

        :param key: Either the name or index of the column requested.
        :type key: str or int
        """
        (pos, name) = self._get_pos(key)
        self._set_column(name, pos, None)

    def __iter__(self):
        """
        Iterate over the names of the columns.
        """
        return iter(self._table._columns)

    def __len__(self):
        """
        Returnt the number of columns.
        """
        return len(self._table._columns)

    # Internals

    def _get_text(self, value):
        """
        Translate the given value to a text string.  The default
        implementation passes this to the table class for conversion.
        """
        return self._table._get_text(value)

    def _get_pos(self, name):
        """
        Given a name or index, find the piece of information that's missing
        and return both.

        :param name: Name of a column (``str``) or index (``int``).
        :type name: str or int
        """
        if isinstance(name, int):
            return (name, self._table._columns[name])
        else:
            return (self._table._columns_by_name[name], name)

    def _set_column(self, name, pos, value):
        """
        Set the value of a column, updating the underlying Treeview at the
        same time.
        """
        self._columns[pos] = value

        if self._iid is not None:
            # Stringify "text" in case it's an object
            self._table._treeview.set(self._iid, name, self._get_text(value))


# The component
class Table(ttk.Frame, MutableSequence):
    _ITEM_CLASS = TableItem

    """
    Table component for Tkinter applications.  This can be sub-classed by
    applications to customise the behaviour.
    """

    def __init__(
        self,
        parent,
        columns=None,
        multiselect=False,
        on_select=None,
        **kwargs
    ):
        """
        Create a new Table object.

        :param parent:      Tkinter parent object
        :type parent:       class:`tkinter.Widget`
        :param columns:     The columns and their labels, a sequence of
                            two-element tuples of the form ``(name, title)``.
        :type columns:      class:`Sequence`
        :param multiselect: Whether we allow selecting multiple rows or not?
        :type multiselect:  boolean
        :param on_select:   Call-back function when an item is selected
        :type on_select:    function
        """
        if columns is None:
            columns = ()

        super(Table, self).__init__(parent, **kwargs)

        self._columns = tuple(c[0] for c in columns)
        self._columns_by_name = dict(
            (name, pos) for pos, name in enumerate(self._columns)
        )
        self._items = []
        self._multiselect = multiselect
        self._on_select = on_select

        self._treeview = ttk.Treeview(
            self,
            columns=self._columns,
            selectmode="extended" if multiselect else "browse",
        )
        self._treeview.grid(
            row=0,
            column=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )
        self._treeview.bind("<<TreeviewSelect>>", self._on_tvselect)

        # Set up headings
        for name, label in columns:
            self._treeview.heading(name, text=self._get_text(label))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    # Selection API

    @property
    def selection(self):
        """
        Retrieve the selections made on the table.

        If ``multiselect`` is ``True``:
            a ``set`` of indices is returned.  If nothing is selected,
            an empty ``set`` is returned.

        Else if ``multiselect`` is ``False``:
            the index of the row selected is returned.
            If nothing is selected, ``None`` is returned.
        """
        selection = self._treeview.selection()
        if self._multiselect:
            return set(self._treeview.index(iid) for iid in selection)
        else:
            try:
                return self._treeview.index(selection[0])
            except IndexError:
                return None

    @selection.setter
    def selection(self, indices):
        """
        Replace the selections made on the table.

        If ``indices`` is ``None``:
            De-select all rows.

        Else if ``multiselect`` is ``True``:
            ``indices`` is either a single index, or a sequence of indices.
            These rows will be selected (and others de-selected).

        Else if ``multiselect`` is ``False``:
            ``indices`` is an integer row index.  It will be selected.
        """
        if indices is None:
            # De-select all
            selection = ()
        elif self._multiselect:
            # Set multi-selection
            if not isinstance(indices, Sequence):
                indices = (indices,)
            selection = tuple(self._items[idx]._iid for idx in indices)
        else:
            # Set single-selection
            selection = (self._items[indices]._iid,)

        self._treeview.selection_set(*selection)

    def selection_add(self, *indices):
        """
        Add the indicated rows (given by row index) to the current selection
        without de-selecting other rows.  Requires ``multiselect`` set to
        ``True``.
        """
        self._selection_update("add", *indices)

    def selection_remove(self, *indices):
        """
        Remove the indicated rows (given by row index) to the current selection
        without de-selecting other rows.  Requires ``multiselect`` set to
        ``True``.
        """
        self._selection_update("remove", *indices)

    def selection_toggle(self, *indices):
        """
        Toggle the indicated rows (given by row index) to the current selection
        without de-selecting other rows.  Requires ``multiselect`` set to
        ``True``.
        """
        self._selection_update("toggle", *indices)

    @property
    def on_select(self):
        """
        Return the callback called when a selection is changed.
        """
        return self._on_select

    @on_select.setter
    def on_select(self, callback):
        """
        Change the callback called when a selection is changed.
        """
        self._on_select = callback

    # MutableSequence interface

    def __getitem__(self, idx):
        """
        Return the item on row ``idx``; if there's an object reference, return
        the object reference itself, otherwise just return the ``TableItem``.
        """
        item = self._items[idx]
        if item.objectref is not None:
            return item.objectref
        else:
            return item

    def __setitem__(self, idx, itemdata):
        """
        Replace the data for row ``idx``.  ``itemdata`` can take a couple of
        forms:

        - Bare value: ``itemdata`` will be stringified and used for the row
          label value.
        - Two-element tuple ``(value, columndict)``: ``value`` will be
          stringified and used as the row label value.  ``columndict`` is a
          mapping of column names to _their_ values for this row: again, all
          will be stringified for display purposes.
        - N-element tuple: N > 1; the first element of the tuple is taken as
          the row value, the remainder is the values of each column.
        """
        (value, columns, objectref) = self._getobject(itemdata)
        item = self._items[idx]
        item.value = value
        item.objectref = objectref
        for pos, col in enumerate(columns):
            item[pos] = col

    def __delitem__(self, idx):
        """
        Remove the row at index ``idx``.
        """
        item = self._items[idx]
        self._treeview.delete(item._iid)
        self._items.pop(idx)

    def __len__(self):
        """
        Return the number of rows in the table.
        """
        return len(self._items)

    def insert(self, idx, itemdata):
        """
        Insert a new row into the table.  See ``__setitem__`` above.
        """
        (value, columns, objectref) = self._getobject(itemdata)
        iid = self._treeview.insert(
            "",
            idx,
            text=str(value),
            values=tuple(self._get_text(c) for c in columns),
        )
        item = self._ITEM_CLASS(
            table=self,
            value=value,
            columns=columns,
            iid=iid,
            objectref=objectref,
        )
        self._items.insert(idx, item)

    # Internals

    def _selection_update(self, method, *indices):
        if not self._multiselect:
            raise NotImplementedError("This is not a multi-select table")

        getattr(self._treeview, "selection_%s" % method)(
            *(self._items[idx]._iid for idx in indices)
        )

    def _getobject(self, itemdata):
        """
        Extract the row information and object reference from the given
        object.  Sub-classes may override this, returning a tuple of the form:
        ``(rowvalue, columnvalues, objectref)``.
        """
        if isinstance(itemdata, str):
            # Assume plain row with no column data
            value = itemdata
            columns = (None,) * len(self._columns)
        elif isinstance(itemdata, Sequence):
            # Row with column data
            value = itemdata[0]
            if isinstance(itemdata[1], Mapping):
                # Columns given as a dict, convert to tuple
                columns = tuple(itemdata[1].get(c) for c in self._columns)
            else:
                columns = tuple(itemdata[1:])

            if len(columns) < len(self._columns):
                # Pad the columns
                columns += (None,) * (len(self._columns) - len(columns))
        else:
            raise TypeError(
                "Don't know how to handle type %s" % type(itemdata)
            )

        return (value, columns, None)

    def _get_text(self, value):
        """
        Conversion of a value to a string.  This simple version returns an
        empty string for ``None``, and ``str(value)`` for everything else.

        This may be customised in a sub-class for special handling.
        """
        if value is None:
            return ""
        else:
            return str(value)

    def _on_tvselect(self, *args):
        if self.on_select is not None:
            self.on_select(self, self.selection)


# Example usage
if __name__ == "__main__":
    print("Running Table example")
    tk = tkinter.Tk()

    def _on_select(tbl, selection):
        print("Selected: %r" % selection)

    widget = Table(
        parent=tk,
        columns=[("a", "Column A"), ("b", "Column B"), ("c", "Column C")],
        on_select=_on_select,
    )
    widget.append("A bare string")
    widget.append(("String with column data (tuple)", 111, 222, 333))
    widget.append("To be deleted")
    widget.append(
        ("String with column data (dict)", {"a": 444, "b": 555, "c": 666})
    )
    widget.append("Bare string, will be added to later")

    widget.selection = 1
    print(widget.selection)

    del widget[2]
    widget[3]["a"] = 123
    widget[3]["b"] = 456
    widget[3]["c"] = 789

    widget.pack(fill="both", expand=True)
    tk.mainloop()
