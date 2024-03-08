#!/usr/bin/env python3

"""
A drop-down list widget that takes an Enum for its input.
"""

# © 2024 Stuart Longland VK4MSL
# SPDX-License-Identifier: Python-2.0

# GUI stuff
import tkinter
from tkinter import ttk


# The component
class EnumList(ttk.Frame):
    """
    Drop-down list box using Enums.  Sorting and label generation can be
    customised through subclassing.
    """

    def __init__(
        self,
        parent,
        enum,
        value=None,
        on_select=None,
        add_none=False,
        reverse=False,
        **kwargs
    ):
        """
        Create a new EnumList object.

        :param parent:      Tkinter parent object
        :type parent:       class:`tkinter.Widget`
        :param enum:        The enumeration that represents the possible
                            values.
        :type enum:         class:`Enum`
        :param on_select:   Call-back function when an item is selected
        :type on_select:    function
        :param add_none:    Add an option for ``None``
        :type add_none:     boolean
        :param reverse:     Reverse the sort order
        :type reverse:      boolean
        """
        super(EnumList, self).__init__(parent, **kwargs)

        self._enum = enum
        self._on_select = on_select
        self._add_none = add_none
        self._reverse = reverse
        (self._values, self._labels) = self._enumerate_enum()
        self._values_rmap = dict(
            (value, posn) for (posn, value) in enumerate(self._values)
        )

        self._label_var = tkinter.StringVar(value=self._get_text(value))
        self._listbox = ttk.Combobox(self, textvariable=self._label_var)
        self._listbox["values"] = self._labels
        self._listbox.state(["readonly"])
        self._listbox.grid(
            row=0,
            column=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )
        self._listbox.bind("<<ComboboxSelected>>", self._on_lbselect)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    # Selection API

    @property
    def text(self):
        """
        Return the human-readable selection text value.
        """
        return self._label_var.get()

    @property
    def selection(self):
        """
        Retrieve the currently selected enum value.
        """
        # current() returns the index of the current value or -1 if the current value is
        # not in the values list.
        selection = self._listbox.current()
        if selection < 0:
            return None
        else:
            return self._values[selection]

    @selection.setter
    def selection(self, value):
        """
        Select one of the possible enum values, or none of them if ``None``.
        """
        if value is None:
            self._listbox.current(-1)
        else:
            self._listbox.current(self._values_rmap[self._enum(value)])

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

    # Internals

    def _enumerate_enum(self):
        """
        Enumerate all possible values and their labels for the enum.

        Returns (tuple_of_values, tuple_of_labels)
        """
        if self._add_none:
            options = (None,) + tuple(self._enum)
        else:
            options = tuple(self._enum)

        # Generates a list of [(enumvalue, enumlabel)]
        labelled_values = sorted(
            ((value, self._get_text(value)) for value in options),
            key=lambda i: self._get_sort_key(*i),
            reverse=self._reverse,
        )

        # Split these into two separate tuples, return as a 2-element tuple of
        # tuples.
        return tuple(zip(*labelled_values))

    def _get_sort_key(self, value, label):
        """
        Return the sort order key for the enumeration.  The default
        implementation sorts by text label ascending, this can be overridden
        in a sub-class.
        """
        return label

    def _get_text(self, value):
        """
        Conversion of a value to a string.  This simple version returns the
        "name" of the enum value, or an empty string for ``None``.

        This may be customised in a sub-class for special handling.
        """
        if value is None:
            return ""
        else:
            return value.name

    def _on_lbselect(self, *args):
        if self.on_select is not None:
            self.on_select(self, self.selection)


# Example usage
if __name__ == "__main__":
    from enum import Enum

    print("Running EnumList example")
    tk = tkinter.Tk()

    class TestEnum(Enum):
        EnumA = 1
        EnumB = 2
        EnumC = 3

    def _on_select(lst, selection):
        print("Selected: %r" % selection)

    widget = EnumList(
        parent=tk, enum=TestEnum, on_select=_on_select, add_none=True
    )

    assert widget.selection is None
    assert widget.text == ""

    widget.selection = 2  # EnumB
    print(widget.selection)

    widget.pack(fill="both", expand=True)
    tk.mainloop()
