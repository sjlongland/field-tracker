#!/usr/bin/env python3

"""
A drop-down list widget that takes an Enum for its input.
"""

# © 2024 Stuart Longland VK4MSL
# SPDX-License-Identifier: Python-2.0

# GUI stuff
from .objectlist import ObjectList


# The component
class EnumList(ObjectList):
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
        values = list(enum)
        if add_none:
            values.insert(0, None)

        self._enum = enum

        super(EnumList, self).__init__(
            parent,
            values=values,
            value=value,
            on_select=on_select,
            reverse=reverse,
            **kwargs
        )

    # Internals

    def _get_identity(self, value):
        """
        Cast the value to the Enum value.
        """
        if value is None:
            return None

        return self._enum(value)

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


# Example usage
if __name__ == "__main__":
    from enum import Enum
    import tkinter

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
