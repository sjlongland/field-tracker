#!/usr/bin/env python3

# Event set-up dialogue.  Mimics the page of the same name in the WICEN RFID
# Operator UI.  Serves to capture the specifics of the event being managed:
# - name of the event
# - start/finish time
# - events (rides)
# - check-point locations

# GUI stuff
import tkinter
from tkinter import ttk, messagebox
from ..components.buttonbox import ButtonBox
from ..components.enumlist import EnumList

# Time-zone data
import zoneinfo

# Custom dialogues and setup-specific widgets
from .location import LocationTable, LocationEditDialogue
from .division import DivisionTable, DivisionEditDialogue

from ..model import (
    Division,
    Location,
    Stage,
    Competitor,
    Checkpoint,
    EventType
)


class EventTypeList(EnumList):
    def __init__(self, parent, **kwargs):
        super(EventTypeList, self).__init__(parent, EventType, **kwargs)

    def _get_text(self, value):
        return value.data.name


# .---------------------------- Event Set-up -------------------------------.
# | .------------------------- Event Details -----------------------------. |
# | |             .--------------.---.          .-----------------------. | |
# | | Event Type  |              | v |     Name |                       | | |
# | |             '--------------'---'          '-----------------------' | |
# | |             .------------------.          .-----------------------. | |
# | | Auth. Org.  |                  | Location |                       | | |
# | |             '------------------'          '-----------------------' | |
# | |             .------------------.          .-----------------------. | |
# | | Start Date  |                  | End Date |                       | | |
# | |             '------------------'          '-----------------------' | |
# | |             .-------------------------------------------------.---. | |
# | | Time-Zone   |                                                 | v | | |
# | |             '-------------------------------------------------'---' | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .----------------------------- Locations -----------------------------. |
# | | .----.-----------------------------.--------------------. .-------. | |
# | | | #  | Name                        | Time-zone          | |  Add  | | |
# | | |----|-----------------------------|--------------------| '-------' | |
# | | |    |                             |                    | .-------. | |
# | | |    |                             |                    | |  Edit | | |
# | | |    |                             |                    | '-------' | |
# | | |    |                             |                    | .-------. | |
# | | |    |                             |                    | |  Del  | | |
# | | |    |                             |                    | '-------' | |
# | | |    |                             |                    |           | |
# | | |    |                             |                    |           | |
# | | '----'-----------------------------'--------------------'           | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .----------------------------- Divisions -----------------------------. |
# | | .----.-----------------------------.----------.---------. .-------. | |
# | | | #  | Name                        | Start    | End     | |  Add  | | |
# | | |----|-----------------------------|----------|---------| '-------' | |
# | | |    |                             |          |         | .-------. | |
# | | |    |                             |          |         | |  Edit | | |
# | | |    |                             |          |         | '-------' | |
# | | |    |                             |          |         | .-------. | |
# | | |    |                             |          |         | |Detail | | |
# | | |    |                             |          |         | '-------' | |
# | | |    |                             |          |         | .-------. | |
# | | |    |                             |          |         | |  Del  | | |
# | | '----'-----------------------------'----------'---------' '-------' | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .---------------------------------------------------------------------. |
# | |                             CREATE EVENT                            | |
# | '---------------------------------------------------------------------' |
# '-------------------------------------------------------------------------'
class EventSetupDialogue(object):
    @classmethod
    def show(cls, parent, event, **kwargs):
        tl = tkinter.Toplevel(parent)
        dlg = cls(parent=tl, event=event, **kwargs)
        tl.transient(parent)  # dialog window is related to main
        tl.wait_visibility()  # can't grab until window appears, so we wait
        tl.grab_set()  # ensure all input goes to our window
        tl.wait_window()  # block until window is destroyed

        return dlg._committed

    def __init__(self, event, parent=None):
        if parent is None:
            parent = tkinter.Tk()

        self._db = event.db
        self._event = event
        self._log = event._log.getChild("ui")
        self._locations = {}
        self._divisions = {}
        self._committed = False

        # Refresh direct references if known
        if event.entity_id is not None:
            for loc in db.fetch(Location, {"event_id": event.entity_id}):
                self._log.debug("Fetched location from db: %r", loc)
                self._locations[loc.ref] = loc

            for div in db.fetch(Division, {"event_id": event.entity_id}):
                self._log.debug("Fetched division from db: %r", div)
                self._divisions[div.ref] = div

        # Amend to-be-committed entities
        for loc in event.get_references(Location):
            self._log.debug(
                "Fetched uncommitted location from memory: %r", loc
            )
            self._locations[loc.ref] = loc

        for div in event.get_references(Division):
            self._log.debug(
                "Fetched uncommitted division from memory: %r", div
            )
            self._divisions[div.ref] = div

        self._parent = parent
        self._parent.title("Event Set-up")
        self._window = ttk.Panedwindow(self._parent, orient=tkinter.VERTICAL)

        # Event set-up pane
        self._evtsetup_frame = ttk.Labelframe(
            self._window, text="Event Detail"
        )

        evttype_lbl = ttk.Label(self._evtsetup_frame, text="Event Type")
        evttype_lbl.grid(column=0, row=0)
        self._evttype_lst = EventTypeList(
            self._evtsetup_frame, value=next(iter(EventType))
        )
        self._evttype_lst.grid(column=1, row=0, sticky=(tkinter.W, tkinter.E))

        evtname_lbl = ttk.Label(self._evtsetup_frame, text="Event Name")
        evtname_lbl.grid(column=2, row=0)
        self._evtname_var = tkinter.StringVar(
            value=event.uservalue["event_name"]
        )
        self._evtname_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._evtname_var
        )
        self._evtname_ent.grid(column=3, row=0, sticky=(tkinter.W, tkinter.E))

        authorg_lbl = ttk.Label(
            self._evtsetup_frame, text="Authorizing Organisation"
        )
        authorg_lbl.grid(column=0, row=1)
        self._authorg_var = tkinter.StringVar(
            value=event.uservalue["auth_org"]
        )
        self._authorg_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._authorg_var
        )
        self._authorg_ent.grid(column=1, row=1, sticky=(tkinter.W, tkinter.E))

        location_lbl = ttk.Label(self._evtsetup_frame, text="Location")
        location_lbl.grid(column=2, row=1)
        self._location_var = tkinter.StringVar(
            value=event.uservalue["location"]
        )
        self._location_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._location_var
        )
        self._location_ent.grid(
            column=3, row=1, sticky=(tkinter.W, tkinter.E)
        )

        startdate_lbl = ttk.Label(self._evtsetup_frame, text="Start Date")
        startdate_lbl.grid(column=0, row=2)
        self._startdate_var = tkinter.StringVar(
            value=event.uservalue["start_date"]
        )
        self._startdate_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._startdate_var
        )
        self._startdate_ent.grid(
            column=1, row=2, sticky=(tkinter.W, tkinter.E)
        )

        enddate_lbl = ttk.Label(self._evtsetup_frame, text="End Date")
        enddate_lbl.grid(column=2, row=2)
        self._enddate_var = tkinter.StringVar(
            value=event.uservalue["end_date"]
        )
        self._enddate_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._enddate_var
        )
        self._enddate_ent.grid(column=3, row=2, sticky=(tkinter.W, tkinter.E))

        evttz_lbl = ttk.Label(self._evtsetup_frame, text="Time-zone")
        evttz_lbl.grid(column=0, row=3)
        self._evttz_var = tkinter.StringVar(value=event.uservalue["event_tz"])
        self._evttz_lst = ttk.Combobox(
            self._evtsetup_frame, textvariable=self._evttz_var
        )
        self._evttz_lst.state(["readonly"])
        self._evttz_lst["values"] = ("LOCAL",) + tuple(
            sorted(zoneinfo.available_timezones())
        )
        self._evttz_lst.grid(
            column=1,
            row=3,
            columnspan=3,
            rowspan=1,
            sticky=(tkinter.W, tkinter.E),
        )

        self._evtsetup_frame.columnconfigure(1, weight=1)
        self._evtsetup_frame.columnconfigure(3, weight=1)
        self._window.add(self._evtsetup_frame, weight=3)

        # Locations pane

        self._locations_frame = ttk.Labelframe(self._window, text="Locations")
        self._loc_tbl = LocationTable(self._locations_frame)
        self._loc_tbl.grid(
            column=0,
            row=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )

        loc_buttons = ButtonBox(
            parent=self._locations_frame, orientation=tkinter.VERTICAL
        )
        loc_buttons.add_button("Add", command=self._add_location)
        loc_buttons.add_button("Edit", command=self._edit_location)
        loc_buttons.add_button("Delete", command=self._delete_location)
        loc_buttons.grid(column=1, row=0, sticky=(tkinter.N, tkinter.S))

        self._locations_frame.columnconfigure(0, weight=1)
        self._locations_frame.rowconfigure(0, weight=1)
        self._window.add(self._locations_frame, weight=3)

        # Divisions pane

        self._divisions_frame = ttk.Labelframe(self._window, text="Divisions")
        self._div_tbl = DivisionTable(self._divisions_frame)
        self._div_tbl.grid(
            column=0,
            row=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )

        div_buttons = ButtonBox(
            parent=self._divisions_frame, orientation=tkinter.VERTICAL
        )
        div_buttons.add_button("Add", command=self._add_division)
        div_buttons.add_button("Edit", command=self._edit_division)
        div_buttons.add_button("Delete", command=self._delete_division)
        div_buttons.grid(column=1, row=0, sticky=(tkinter.N, tkinter.S))

        self._divisions_frame.columnconfigure(0, weight=1)
        self._divisions_frame.rowconfigure(0, weight=1)
        self._window.add(self._divisions_frame, weight=3)

        self._buttons = ButtonBox(self._window)
        self._buttons.add_button("COMMIT", command=self._commit)
        self._buttons.add_button("CLOSE", command=self._dismiss)
        self._buttons.grid(column=0, row=2, columnspan=4, rowspan=1)
        self._window.add(self._buttons, weight=1)

        self._refresh_locations()
        self._refresh_divisions()

    def _add_location(self):
        num = 1
        try:
            num += max(loc["loc_num"] for loc in self._locations.values())
        except ValueError:
            pass

        loc = self._db.create(
            Location,
            event_id=self._event,
            loc_num=num,
            loc_tz="EVENT",
            loc_name="Location %d" % num,
        )
        result = LocationEditDialogue.show(
            parent=self._window,
            title="New Location",
            location=loc,
        )
        if result:
            self._locations[loc.ref] = loc
        else:
            loc.delete = True

        self._refresh_locations()

    def _edit_location(self):
        idx = self._loc_tbl.selection
        loc = self._loc_tbl[idx]
        assert isinstance(loc, Location)

        result = LocationEditDialogue.show(
            parent=self._window,
            title="Edit Location: %s" % loc["loc_name"],
            location=loc,
        )

        if result:
            self._locations[loc.ref] = loc

        self._refresh_locations()

    def _delete_location(self):
        idx = self._loc_tbl.selection
        loc = self._loc_tbl[idx]
        assert isinstance(loc, Location)

        self._locations.pop(loc.ref, None)
        loc.delete = True
        del self._loc_tbl[idx]

        self._refresh_locations()

    def _refresh_locations(self):
        locations = list(self._locations.values())
        locations.sort(key=lambda loc: loc["loc_num"])

        # Drop excess elements
        while len(self._loc_tbl) > len(locations):
            del self._loc_tbl[len(locations) - 1]

        # Update existing rows
        for idx, loc in enumerate(locations[0 : len(self._loc_tbl)]):
            self._loc_tbl[idx] = loc

        # Add new rows
        for loc in locations[len(self._loc_tbl) :]:
            self._loc_tbl.append(loc)

    def _add_division(self):
        num = 1
        try:
            num += max(div["div_num"] for div in self._divisions.values())
        except ValueError:
            pass

        div = self._db.create(
            Division,
            event_id=self._event,
            div_num=num,
            div_name="Division %d" % num,
            start_date=self._event["start_date"],
            end_date=self._event["end_date"],
        )
        result = DivisionEditDialogue.show(
            parent=self._window, title="New Division", division=div
        )
        if result:
            self._divisions[div.ref] = div
        else:
            div.delete = True

        self._refresh_divisions()

    def _edit_division(self):
        idx = self._div_tbl.selection
        div = self._div_tbl[idx]
        assert isinstance(div, Division)

        result = DivisionEditDialogue.show(
            parent=self._window,
            title="Edit Division: %s" % div["div_name"],
            division=div,
        )

        if result:
            self._divisions[div.ref] = div

        self._refresh_divisions()

    def _delete_division(self):
        idx = self._div_tbl.selection
        div = self._div_tbl[idx]
        assert isinstance(div, Division)

        self._divisions.pop(div.ref, None)
        div.delete = True
        del self._div_tbl[idx]

        self._refresh_divisions()

    def _refresh_divisions(self):
        divisions = list(self._divisions.values())
        divisions.sort(key=lambda div: div["div_num"])

        # Drop excess elements
        while len(self._div_tbl) > len(divisions):
            del self._div_tbl[len(divisions) - 1]

        # Update existing rows
        for idx, div in enumerate(divisions[0 : len(self._div_tbl)]):
            self._div_tbl[idx] = div

        # Add new rows
        for div in divisions[len(self._div_tbl) :]:
            self._div_tbl.append(div)

    def _commit(self):
        try:
            try:
                self._event["event_type"] = self._evttype_lst.selection
                self._event.uservalue["event_name"] = self._evtname_var.get()
                self._event.uservalue["auth_org"] = self._authorg_var.get()
                self._event.uservalue["location"] = self._location_var.get()
                self._event.uservalue[
                    "start_date"
                ] = self._startdate_var.get()
                self._event.uservalue["end_date"] = self._enddate_var.get()
                self._event.uservalue["event_tz"] = self._evttz_var.get()
            except ValueError as e:
                self._log.error("Event validation failed", exc_info=1)
                messagebox.showerror(message=str(e))
                return

            self._log.debug("Committing event")
            # Validation passes, everything else has been checked, let's
            # commit it to the database.
            statements = []

            # Look for deletions of checkpoints first
            statements.extend(
                cpt.dbvalue.statement
                for cpt in self._db.get_deletions(Checkpoint)
            )

            # Now stages
            statements.extend(
                stg.dbvalue.statement for stg in self._db.get_deletions(Stage)
            )

            # Now competitors
            statements.extend(
                cmp.dbvalue.statement
                for cmp in self._db.get_deletions(Competitor)
            )

            # Finally divisions
            statements.extend(
                div.dbvalue.statement
                for div in self._db.get_deletions(Division)
            )

            # Gather up the insert/update changes.
            statements.append(self._event.dbvalue.statement)
            statements.extend(
                loc.dbvalue.statement
                for loc in self._event.get_references(Location)
            )

            for div in self._event.get_references(Division):
                self._log.debug("Inspecting division %s", div)
                statements.append(div.dbvalue.statement)
                statements.extend(
                    cmp.dbvalue.statement
                    for cmp in div.get_references(Competitor)
                )

                for stg in div.get_references(Stage):
                    self._log.debug(
                        "Inspecting division %s stage %s", div, stg
                    )
                    statements.append(stg.dbvalue.statement)
                    statements.extend(
                        cpt.dbvalue.statement
                        for cpt in stg.get_references(Checkpoint)
                    )

            self._log.debug("%d statements before filtering", len(statements))
            statements = list(filter(lambda s: s is not None, statements))
            self._log.debug("%d statements after filtering", len(statements))

            if statements:
                self._db.commit(statements)
        except Exception as e:
            self._log.error("Change set commit failed", exc_info=1)
            messagebox.showerror(
                message="Failed to commit changes: %s" % (e,)
            )
            return

        self._committed = True
        self._close()

    def _dismiss(self):
        self._event.revert()
        self._committed = False
        self._close()

    def _close(self):
        self._parent.grab_release()
        self._parent.destroy()


if __name__ == "__main__":
    import logging
    import datetime
    from ..model.db import Database
    from ..model import Event

    logging.basicConfig(level=logging.DEBUG)

    db = Database("test.sqlite3")
    db.init()

    # See if there's an event already
    events = list(db.fetch(Event))
    if events:
        evt = events[-1]
    else:
        now = datetime.datetime.now()
        evt = db.create(
            Event,
            event_name="Test Event",
            start_date=now.date(),
            end_date=(now + datetime.timedelta(days=1)).date(),
        )

    tk = tkinter.Tk()
    esd = EventSetupDialogue(parent=tk, event=evt)
    esd._window.pack(fill="both", expand=True)
    tk.mainloop()
