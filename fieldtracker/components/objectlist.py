#!/usr/bin/env python3

"""
A drop-down list widget that takes arbtrary objects for input.
"""

# © 2024 Stuart Longland VK4MSL
# SPDX-License-Identifier: Python-2.0

# GUI stuff
import tkinter
from tkinter import ttk


# The component
class ObjectList(ttk.Frame):
    """
    Drop-down list box using arbitrary object instances.  Sorting and label
    generation can be customised through subclassing.
    """

    def __init__(
        self,
        parent,
        values,
        value=None,
        on_select=None,
        add_none=False,
        reverse=False,
        **kwargs
    ):
        """
        Create a new ObjectList object.

        :param parent:      Tkinter parent object
        :type parent:       class:`tkinter.Widget`
        :param values:      The possible selection values permitted.
        :type values:       class:`Sequence`
        :param on_select:   Call-back function when an item is selected
        :type on_select:    function
        :param reverse:     Reverse the sort order
        :type reverse:      boolean
        """
        super(ObjectList, self).__init__(parent, **kwargs)

        self._on_select = on_select
        self._reverse = reverse
        (self._values, self._labels) = self._enumerate_values(values)
        self._values_rmap = dict(
            (self._get_identity(value), posn)
            for (posn, value) in enumerate(self._values)
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
            self._listbox.current(
                self._values_rmap[self._get_identity(value)]
            )

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

    def _get_identity(self, value):
        """
        Return an identifier for the value provided.  This is used to select a
        specific value key.  The default implementation returns the object's
        ``id()`` (in CPython; this function returns the C pointer.)
        """
        return id(value)

    def _enumerate_values(self, values):
        """
        Enumerate all possible values and their labels.

        Returns (tuple_of_values, tuple_of_labels)
        """
        # Generates a list of [(enumvalue, enumlabel)]
        labelled_values = sorted(
            ((value, self._get_text(value)) for value in values),
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
        result of ``str(value)``, or an empty string for ``None``.

        This may be customised in a sub-class for special handling.
        """
        if value is None:
            return ""
        else:
            return str(value)

    def _on_lbselect(self, *args):
        if self.on_select is not None:
            self.on_select(self, self.selection)


# Example usage
if __name__ == "__main__":
    print("Running ObjectList example")
    tk = tkinter.Tk()

    class MyObjectClass(object):
        def __init__(self, label):
            self._label = label

        def __str__(self):
            return self._label

        def __repr__(self):
            return "%s(%r)" % (self.__class__.__name__, self._label)

    values = [
        None,
        MyObjectClass("Option 1"),
        MyObjectClass("Option 2"),
        MyObjectClass("Option 3"),
    ]

    def _on_select(lst, selection):
        print("Selected: %r" % selection)

    widget = ObjectList(parent=tk, values=values, on_select=_on_select)

    assert widget.selection is None
    assert widget.text == ""

    widget.selection = values[2]  # Option 2
    print(widget.selection)

    widget.pack(fill="both", expand=True)
    tk.mainloop()
