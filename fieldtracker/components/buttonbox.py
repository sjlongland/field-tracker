#!/usr/bin/env python3

# Button box component, lays out buttons in a horizontal or vertical layout
# evenly.

# © 2024 Stuart Longland VK4MSL
# SPDX-License-Identifier: Python-2.0

# GUI stuff
import tkinter
from tkinter import ttk


# The component
class ButtonBox(ttk.Frame):
    def __init__(
        self, parent, orientation=tkinter.HORIZONTAL, weight=1, **kwargs
    ):
        super(ButtonBox, self).__init__(parent, **kwargs)

        if orientation == tkinter.HORIZONTAL:
            self.columnconfigure(0, weight=weight)
        elif orientation == tkinter.VERTICAL:
            self.rowconfigure(0, weight=weight)
        else:
            raise ValueError(
                "Expected orientation to be tkinter.HORIZONTAL or "
                "tkinter.VERTICAL, got %r" % orientation
            )

        self._orientation = orientation
        self._buttons = []
        self._next_pos = 0

    def add_button(
        self,
        text,
        command,
        span=1,
        weight=1,
        sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        **kwargs
    ):
        btn = ttk.Button(self, text=text, command=command)
        self._buttons.append(btn)
        pos = self._next_pos
        self._next_pos += span

        if self._orientation == tkinter.HORIZONTAL:
            btn.grid(
                row=0, column=pos, rowspan=1, columnspan=span, sticky=sticky
            )
            self.columnconfigure(pos, weight=weight)
        else:
            btn.grid(
                row=pos, column=0, rowspan=span, columnspan=1, sticky=sticky
            )
            self.rowconfigure(pos, weight=weight)

        return self


# Example usage
if __name__ == "__main__":
    print("Running button box example")
    tk = tkinter.Tk()

    def _pressed(x, *a):
        print("%r pressed (a=%r)" % (x, a))

    widget = ButtonBox(parent=tk)
    widget.add_button("Button 1", command=lambda *a: _pressed("B1", *a))
    widget.add_button("Button 2", command=lambda *a: _pressed("B2", *a))
    widget.add_button("Button 3", command=lambda *a: _pressed("B3", *a))
    widget.pack(fill="both", expand=True)
    tk.mainloop()
