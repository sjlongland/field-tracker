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
from .components.buttonbox import ButtonBox
from .components.table import Table

# Time-zone data
import zoneinfo

# Event type data and model
from .model.eventtype import EVENT_TYPES
from .model.db import Division, Event, Location, Stage, Competitor, Checkpoint


class _LocationTable(Table):
    def __init__(self, parent, **kwargs):
        super(_LocationTable, self).__init__(
            parent, columns=(("tz", "Time-Zone"),), **kwargs
        )

    def _getobject(self, location):
        return (
            "%d. %s" % (location["loc_num"], location["loc_name"]),
            (location["loc_tz"],),
            location,
        )


# .------------------------------- New Location ----------------------------.
# |       .-----.      .--------------------------------------------------. |
# | Nbr.  |     | Name |                                                  | |
# |       '-----'      '--------------------------------------------------' |
# |            .------------------------------------------------------.---. |
# | Time-Zone  |                                                      | v | |
# |            '------------------------------------------------------'---' |
# | .-----------------------------------. .-------------------------------. |
# | |             COMMIT                | |              CLOSE            | |
# | '-----------------------------------' '-------------------------------' |
# '-------------------------------------------------------------------------'
class _LocationEditDialogue(object):
    @classmethod
    def show(cls, parent, location, **kwargs):
        tl = tkinter.Toplevel(parent)
        dlg = cls(parent=tl, location=location, **kwargs)
        tl.transient(parent)  # dialog window is related to main
        tl.wait_visibility()  # can't grab until window appears, so we wait
        tl.grab_set()  # ensure all input goes to our window
        tl.wait_window()  # block until window is destroyed

        return dlg._committed

    def __init__(
        self,
        title,
        location,
        commit_label="COMMIT",
        close_label="CLOSE",
        parent=None,
    ):
        if parent is None:
            parent = tkinter.Tk()

        self._location = location
        self._log = location._log.getChild("ui")
        self._committed = None
        self._parent = parent
        self._parent.protocol("WM_DELETE_WINDOW", self._dismiss)

        self._window = ttk.Frame(self._parent)

        num_lbl = ttk.Label(self._window, text="Number")
        num_lbl.grid(column=0, row=0)
        self._num_var = tkinter.StringVar(value=location["loc_num"])
        self._num_ent = ttk.Entry(self._window, textvariable=self._num_var)
        self._num_ent.grid(column=1, row=0, sticky=(tkinter.W, tkinter.E))

        name_lbl = ttk.Label(self._window, text="Name")
        name_lbl.grid(column=2, row=0)
        self._name_var = tkinter.StringVar(value=location["loc_name"])
        self._name_ent = ttk.Entry(self._window, textvariable=self._name_var)
        self._name_ent.grid(column=3, row=0, sticky=(tkinter.W, tkinter.E))

        tz_lbl = ttk.Label(self._window, text="Time-zone")
        tz_lbl.grid(column=0, row=1)
        self._tz_var = tkinter.StringVar(value=location["loc_tz"])
        self._tz_lst = ttk.Combobox(self._window, textvariable=self._tz_var)
        self._tz_lst["values"] = (
            "EVENT",
            "LOCAL",
        ) + tuple(sorted(zoneinfo.available_timezones()))
        self._tz_lst.grid(
            column=1,
            row=1,
            columnspan=3,
            rowspan=1,
            sticky=(tkinter.W, tkinter.E),
        )

        buttons = ButtonBox(parent=self._window)
        buttons.add_button(commit_label, command=self._commit)
        buttons.add_button(close_label, command=self._dismiss)
        buttons.grid(
            column=0,
            row=2,
            columnspan=4,
            rowspan=1,
            sticky=(tkinter.E, tkinter.W),
        )
        self._window.columnconfigure(1, weight=1)
        self._window.columnconfigure(3, weight=1)
        self._window.grid()
        self._parent.title(title)

    def _commit(self):
        try:
            self._location.uservalue["loc_num"] = self._num_var.get()
            self._location.uservalue["loc_name"] = self._name_var.get()
            self._location.uservalue["loc_tz"] = self._tz_var.get()
        except ValueError as e:
            messagebox.showerror(message=str(e))
            return

        self._committed = True
        self._close()

    def _dismiss(self):
        self._location.revert()
        self._committed = False
        self._close()

    def _close(self):
        self._parent.grab_release()
        self._parent.destroy()


class _DivisionTable(Table):
    def __init__(self, parent, **kwargs):
        super(_DivisionTable, self).__init__(
            parent,
            columns=(
                ("start_date", "Start Date"),
                ("end_date", "End Date"),
            ),
            **kwargs
        )

    def _getobject(self, division):
        return (
            "%d. %s" % (division["div_num"], division["div_name"]),
            (
                division["start_date"],
                division["end_date"],
            ),
            division,
        )


# .------------------------------- New Division ----------------------------.
# | .------------------------- Division Details --------------------------. |
# | |       .-----.      .----------------------------------------------. | |
# | | Nbr.  |     | Name |                                              | | |
# | |       '-----'      '----------------------------------------------' | |
# | |            .----------------------.          .--------------------. | |
# | | Start Date |                      | End Date |                    | | |
# | |            '----------------------'          '--------------------' | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .--------------------------------- Stages ----------------------------. |
# | | .----.------------------------------------------.-------. .-------. | |
# | | | #  | Name                                     | Order | |  Add  | | |
# | | |----|------------------------------------------|-------| '-------' | |
# | | |    |                                          |       | .-------. | |
# | | |    |                                          |       | |  Edit | | |
# | | |    |                                          |       | '-------' | |
# | | |    |                                          |       | .-------. | |
# | | |    |                                          |       | |  Del  | | |
# | | |    |                                          |       | '-------' | |
# | | |    |                                          |       |           | |
# | | |    |                                          |       |           | |
# | | '----'------------------------------------------'-------'           | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .----------------------------- Competitors ---------------------------. |
# | | .----.----------------------------------------.---------. .-------. | |
# | | | #  | Name                                   | Status  | |  Add  | | |
# | | |----|----------------------------------------|---------| '-------' | |
# | | |    |                                        |         | .-------. | |
# | | |    |                                        |         | |  Edit | | |
# | | |    |                                        |         | '-------' | |
# | | |    |                                        |         | .-------. | |
# | | |    |                                        |         | |  Del  | | |
# | | |    |                                        |         | '-------' | |
# | | |    |                                        |         |           | |
# | | |    |                                        |         |           | |
# | | '----'----------------------------------------'---------'           | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .-----------------------------------. .-------------------------------. |
# | |             COMMIT                | |              CLOSE            | |
# | '-----------------------------------' '-------------------------------' |
# '-------------------------------------------------------------------------'
class _DivisionEditDialogue(object):
    @classmethod
    def show(cls, parent, division, **kwargs):
        tl = tkinter.Toplevel(parent)
        dlg = cls(parent=tl, division=division, **kwargs)
        tl.transient(parent)  # dialog window is related to main
        tl.wait_visibility()  # can't grab until window appears, so we wait
        tl.grab_set()  # ensure all input goes to our window
        tl.wait_window()  # block until window is destroyed
        return dlg._committed

    def __init__(
        self,
        title,
        division,
        commit_label="COMMIT",
        close_label="CLOSE",
        parent=None,
    ):
        if parent is None:
            parent = tkinter.Tk()

        self._db = division.db
        self._division = division
        self._log = division._log.getChild("ui")
        self._stages = {}
        self._competitors = {}
        self._committed = False

        # Refresh direct references if known
        if division.entity_id is not None:
            for stg in db.fetch(Stage, {"div_id": division.entity_id}):
                self._log.debug("Fetched stage from db: %r", stg)
                self._stages[stg.ref] = stg

            for cmp in db.fetch(Competitor, {"div_id": division.entity_id}):
                self._log.debug("Fetched competitor from db: %r", cmp)
                self._competitors[cmp.ref] = cmp

        # Amend to-be-committed entities
        for stg in division.get_references(Stage):
            self._log.debug("Fetched uncommitted stage from memory: %r", stg)
            self._stages[stg.ref] = stg

        for cmp in division.get_references(Competitor):
            self._log.debug(
                "Fetched uncommitted competitor from memory: %r", cmp
            )
            self._competitors[cmp.ref] = cmp

        self._parent = parent
        self._parent.protocol("WM_DELETE_WINDOW", self._dismiss)

        self._window = ttk.Panedwindow(self._parent, orient=tkinter.VERTICAL)

        # Division detail

        self._divdetail_frame = ttk.Labelframe(
            self._window, text="Division Detail"
        )

        num_lbl = ttk.Label(self._divdetail_frame, text="Number")
        num_lbl.grid(column=0, row=0)
        self._num_var = tkinter.StringVar(value=division["div_num"])
        self._num_ent = ttk.Entry(
            self._divdetail_frame, textvariable=self._num_var
        )
        self._num_ent.grid(column=1, row=0, sticky=(tkinter.W, tkinter.E))

        name_lbl = ttk.Label(self._divdetail_frame, text="Name")
        name_lbl.grid(column=2, row=0)
        self._name_var = tkinter.StringVar(value=division["div_name"])
        self._name_ent = ttk.Entry(
            self._divdetail_frame, textvariable=self._name_var
        )
        self._name_ent.grid(column=3, row=0, sticky=(tkinter.W, tkinter.E))

        start_date_lbl = ttk.Label(self._divdetail_frame, text="Start Date")
        start_date_lbl.grid(column=0, row=1)
        self._start_date_var = tkinter.StringVar(value=division["start_date"])
        self._start_date_ent = ttk.Entry(
            self._divdetail_frame, textvariable=self._start_date_var
        )
        self._start_date_ent.grid(
            column=1, row=1, sticky=(tkinter.W, tkinter.E)
        )

        end_date_lbl = ttk.Label(self._divdetail_frame, text="End Date")
        end_date_lbl.grid(column=2, row=1)
        self._end_date_var = tkinter.StringVar(value=division["end_date"])
        self._end_date_ent = ttk.Entry(
            self._divdetail_frame, textvariable=self._end_date_var
        )
        self._end_date_ent.grid(
            column=3, row=1, sticky=(tkinter.W, tkinter.E)
        )

        self._divdetail_frame.columnconfigure(1, weight=1)
        self._divdetail_frame.columnconfigure(3, weight=1)
        self._window.add(self._divdetail_frame, weight=3)

        # Stages pane

        self._stages_frame = ttk.Labelframe(self._window, text="Stages")
        self._stg_tbl = _StageTable(self._stages_frame)
        self._stg_tbl.grid(
            column=0,
            row=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )

        stage_buttons = ButtonBox(
            parent=self._stages_frame, orientation=tkinter.VERTICAL
        )
        stage_buttons.add_button("Add", command=self._add_stage)
        stage_buttons.add_button("Edit", command=self._edit_stage)
        stage_buttons.add_button("Delete", command=self._delete_stage)
        stage_buttons.grid(column=1, row=0, sticky=(tkinter.N, tkinter.S))

        self._stages_frame.columnconfigure(0, weight=1)
        self._stages_frame.rowconfigure(0, weight=1)
        self._window.add(self._stages_frame, weight=3)

        # Competitors pane

        self._competitors_frame = ttk.Labelframe(
            self._window, text="Competitors"
        )
        self._cmp_tbl = _CompetitorTable(self._competitors_frame)
        self._cmp_tbl.grid(
            column=0,
            row=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )

        competitor_buttons = ButtonBox(
            parent=self._competitors_frame, orientation=tkinter.VERTICAL
        )
        competitor_buttons.add_button("Add", command=self._add_competitor)
        competitor_buttons.add_button("Edit", command=self._edit_competitor)
        competitor_buttons.add_button(
            "Delete", command=self._delete_competitor
        )
        competitor_buttons.grid(
            column=1, row=0, sticky=(tkinter.N, tkinter.S)
        )

        self._competitors_frame.columnconfigure(0, weight=1)
        self._competitors_frame.rowconfigure(0, weight=1)
        self._window.add(self._competitors_frame, weight=3)

        buttons = ButtonBox(parent=self._window)
        buttons.add_button(commit_label, command=self._commit)
        buttons.add_button(close_label, command=self._dismiss)
        buttons.grid(
            column=0,
            row=2,
            columnspan=4,
            rowspan=1,
            sticky=(tkinter.E, tkinter.W),
        )
        self._window.add(buttons, weight=1)
        self._window.grid()
        self._parent.title(title)

        self._refresh_stages()
        self._refresh_competitors()

    def _commit(self):
        try:
            self._division.uservalue["div_num"] = self._num_var.get()
            self._division.uservalue["div_name"] = self._name_var.get()
            self._division.uservalue[
                "start_date"
            ] = self._start_date_var.get()
            self._division.uservalue["end_date"] = self._end_date_var.get()
        except ValueError as e:
            messagebox.showerror(message=str(e))
            return

        self._committed = True
        self._close()

    def _dismiss(self):
        self._committed = False
        self._close()

    def _close(self):
        self._parent.grab_release()
        self._parent.destroy()

    def _add_stage(self):
        num = 1
        order = 1
        try:
            num += max(stg["stg_num"] for stg in self._stages.values())
            order += max(stg["stg_order"] for stg in self._stages.values())
        except ValueError:
            pass

        stg = self._db.create(
            Stage,
            div_id=self._division,
            stg_num=num,
            stg_order=order,
            stg_name="Stage %d" % num,
        )
        result = _StageEditDialogue.show(
            parent=self._window,
            title="New Stage",
            stage=stg,
        )
        if result:
            self._stages[stg.ref] = stg
        else:
            stg.delete = True

        self._refresh_stages()

    def _edit_stage(self):
        idx = self._stg_tbl.selection
        stg = self._stg_tbl[idx]
        assert isinstance(stg, Stage)

        result = _StageEditDialogue.show(
            parent=self._window,
            title="Edit Stage: %s" % stg["stg_name"],
            stage=stg,
        )

        if result:
            self._stages[stg.ref] = stg

        self._refresh_stages()

    def _delete_stage(self):
        idx = self._stg_tbl.selection
        stg = self._stg_tbl[idx]
        assert isinstance(stg, Stage)

        self._stages.pop(stg.ref, None)
        del self._stg_tbl[idx]

        self._refresh_stages()

    def _refresh_stages(self):
        stages = list(self._stages.values())
        stages.sort(key=lambda stg: stg["stg_num"])

        # Drop excess elements
        while len(self._stg_tbl) > len(stages):
            del self._stg_tbl[len(stages) - 1]

        # Update existing rows
        for idx, stg in enumerate(stages[0 : len(self._stg_tbl)]):
            self._stg_tbl[idx] = stg

        # Add new rows
        for stg in stages[len(self._stg_tbl) :]:
            self._stg_tbl.append(stg)

    def _add_competitor(self):
        pass

    def _edit_competitor(self):
        pass

    def _delete_competitor(self):
        pass

    def _refresh_competitors(self):
        pass


class _StageTable(Table):
    def __init__(self, parent, **kwargs):
        super(_StageTable, self).__init__(
            parent, columns=(("stg_order", "Order"),), **kwargs
        )

    def _getobject(self, stage):
        return (
            "%d. %s" % (stage["stg_num"], stage["stg_name"]),
            (stage["stg_order"],),
            stage,
        )


class _CompetitorTable(Table):
    def __init__(self, parent, **kwargs):
        super(_CompetitorTable, self).__init__(
            parent,
            columns=(
                ("cmp_name", "Name"),
                ("cmp_status", "Status"),
            ),
            **kwargs
        )

    def _getobject(self, competitor):
        return (
            "%d. %s" % (competitor["cmp_num"], competitor["cmp_name"]),
            (
                competitor["cmp_name"],
                competitor["cmp_status"],
            ),
            competitor,
        )


# .------------------------------- New Stage -------------------------------.
# | .---------------------------- Stage Details --------------------------. |
# | |       .-----.      .----------------------------------------------. | |
# | | Nbr.  |     | Name |                                              | | |
# | |       '-----'      '----------------------------------------------' | |
# | |       .-----.                                                       | |
# | | Ord.  |     |                                                       | |
# | |       '-----'                                                       | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .----------------------------- Checkpoints ---------------------------. |
# | | .----.-----------------------------------.------.-------. .-------. | |
# | | | #  | Name                              | Type | Order | |  Add  | | |
# | | |----|-----------------------------------|------|-------| '-------' | |
# | | |    |                                   |      |       | .-------. | |
# | | |    |                                   |      |       | |  Edit | | |
# | | |    |                                   |      |       | '-------' | |
# | | |    |                                   |      |       | .-------. | |
# | | |    |                                   |      |       | |  Del  | | |
# | | |    |                                   |      |       | '-------' | |
# | | |    |                                   |      |       |           | |
# | | |    |                                   |      |       |           | |
# | | '----'-----------------------------------'------'-------'           | |
# | '---------------------------------------------------------------------' |
# |                                                                         |
# | .-----------------------------------. .-------------------------------. |
# | |             COMMIT                | |              CLOSE            | |
# | '-----------------------------------' '-------------------------------' |
# '-------------------------------------------------------------------------'
class _StageEditDialogue(object):
    @classmethod
    def show(cls, parent, stage, **kwargs):
        tl = tkinter.Toplevel(parent)
        dlg = cls(parent=tl, stage=stage, **kwargs)
        tl.transient(parent)  # dialog window is related to main
        tl.wait_visibility()  # can't grab until window appears, so we wait
        tl.grab_set()  # ensure all input goes to our window
        tl.wait_window()  # block until window is destroyed

        return dlg._committed

    def __init__(
        self,
        title,
        stage,
        commit_label="COMMIT",
        close_label="CLOSE",
        parent=None,
    ):
        if parent is None:
            parent = tkinter.Tk()

        self._db = stage.db
        self._stage = stage
        self._div = stage["div_id"]
        self._log = stage._log.getChild("ui")
        self._checkpoints = {}
        self._locations = {}

        event = self._div["event_id"]

        # Refresh direct references if known
        if stage.entity_id is not None:
            for cpt in db.fetch(Checkpoint, {"stg_id": stage.entity_id}):
                self._log.debug("Fetched checkpoint from db: %r", cpt)
                self._checkpoints[cpt.ref] = cpt

        if event.entity_id is not None:
            for loc in db.fetch(Location, {"event_id": event.entity_id}):
                self._log.debug("Fetched location from db: %r", loc)
                self._checkpoints[loc.ref] = loc

        # Amend to-be-committed entities
        for cpt in stage.get_references(Checkpoint):
            self._log.debug(
                "Fetched uncommitted checkpoint from memory: %r", cpt
            )
            self._checkpoints[cpt.ref] = cpt

        for loc in event.get_references(Location):
            self._log.debug(
                "Fetched uncommitted location from memory: %r", loc
            )
            self._locations[loc.ref] = loc

        self._parent = parent
        self._parent.protocol("WM_DELETE_WINDOW", self._dismiss)

        self._window = ttk.Panedwindow(self._parent, orient=tkinter.VERTICAL)

        # Stage detail

        self._stagedetail_frame = ttk.Labelframe(
            self._window, text="Stage Detail"
        )

        num_lbl = ttk.Label(self._stagedetail_frame, text="Number")
        num_lbl.grid(column=0, row=0)
        self._num_var = tkinter.StringVar(value=stage.uservalue["stg_num"])
        self._num_ent = ttk.Entry(
            self._stagedetail_frame, textvariable=self._num_var
        )
        self._num_ent.grid(column=1, row=0, sticky=(tkinter.W, tkinter.E))

        name_lbl = ttk.Label(self._stagedetail_frame, text="Name")
        name_lbl.grid(column=2, row=0)
        self._name_var = tkinter.StringVar(value=stage.uservalue["stg_name"])
        self._name_ent = ttk.Entry(
            self._stagedetail_frame, textvariable=self._name_var
        )
        self._name_ent.grid(column=3, row=0, sticky=(tkinter.W, tkinter.E))

        order_lbl = ttk.Label(self._stagedetail_frame, text="Order")
        order_lbl.grid(column=0, row=1)
        self._order_var = tkinter.StringVar(
            value=stage.uservalue["stg_order"]
        )
        self._order_ent = ttk.Entry(
            self._stagedetail_frame, textvariable=self._order_var
        )
        self._order_ent.grid(column=1, row=1, sticky=(tkinter.W, tkinter.E))

        self._stagedetail_frame.columnconfigure(1, weight=1)
        self._stagedetail_frame.columnconfigure(3, weight=1)
        self._window.add(self._stagedetail_frame, weight=3)

        # Checkpoints pane

        self._checkpoints_frame = ttk.Labelframe(
            self._window, text="Checkpoints"
        )
        self._cpt_tbl = _CheckpointTable(self._checkpoints_frame)
        self._cpt_tbl.grid(
            column=0,
            row=0,
            sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W),
        )

        cpt_buttons = ButtonBox(
            parent=self._checkpoints_frame, orientation=tkinter.VERTICAL
        )
        cpt_buttons.add_button("Add", command=self._add_checkpoint)
        cpt_buttons.add_button("Edit", command=self._edit_checkpoint)
        cpt_buttons.add_button("Delete", command=self._delete_checkpoint)
        cpt_buttons.grid(column=1, row=0, sticky=(tkinter.N, tkinter.S))

        self._checkpoints_frame.columnconfigure(0, weight=1)
        self._checkpoints_frame.rowconfigure(0, weight=1)
        self._window.add(self._checkpoints_frame, weight=3)

        # Commit / Close buttons

        buttons = ButtonBox(parent=self._window)
        buttons.add_button(commit_label, command=self._commit)
        buttons.add_button(close_label, command=self._dismiss)
        buttons.grid(
            column=0,
            row=2,
            columnspan=4,
            rowspan=1,
            sticky=(tkinter.E, tkinter.W),
        )
        self._window.add(buttons, weight=1)
        self._window.grid()
        self._parent.title(title)

        # self._refresh_checkpoints()

    def _commit(self):
        try:
            self._stage.uservalue["stg_num"] = self._num_var.get()
            self._stage.uservalue["stg_name"] = self._name_var.get()
            self._stage.uservalue["stg_order"] = self._order_var.get()
        except ValueError as e:
            messagebox.showerror(message=str(e))
            return

        self._committed = True
        self._close()

    def _dismiss(self):
        self._committed = False
        self._close()

    def _close(self):
        self._parent.grab_release()
        self._parent.destroy()

    def _add_checkpoint(self):
        num = 1
        try:
            num += max(cpt["cpt_num"] for cpt in self._checkpoints.values())
        except ValueError:
            pass

        # Pick a location for integrity purposes
        try:
            loc = list(self._locations.values())[0]
        except IndexError:
            messagebox.showerror(
                message="You need to create check-point locations first")
            return

        cpt = self._db.create(
            Checkpoint,
            div_id=self._div,
            stg_id=self._stage,
            loc_id=loc,
            cpt_num=num
        )
        result = _CheckpointEditDialogue.show(
            parent=self._window,
            title="New Checkpoint",
            checkpoint=cpt,
            locations=self._locations
        )
        if result:
            self._checkpoints[cpt.ref] = cpt
        else:
            cpt.delete = True

        self._refresh_checkpoints()

    def _edit_checkpoint(self):
        idx = self._cpt_tbl.selection
        cpt = self._cpt_tbl[idx]
        assert isinstance(cpt, Checkpoint)

        result = _CheckpointEditDialogue.show(
            parent=self._window,
            title="Edit Checkpoint %s" % cpt["cpt_num"],
            checkpoint=cpt,
            locations=self._locations
        )

        if result:
            self._checkpoints[cpt.ref] = cpt

        self._refresh_checkpoints()

    def _delete_checkpoint(self):
        idx = self._cpt_tbl.selection
        cpt = self._cpt_tbl[idx]
        assert isinstance(cpt, Checkpoint)

        self._checkpoints.pop(cpt.ref, None)
        del self._cpt_tbl[idx]

        self._refresh_checkpoints()

    def _refresh_checkpoints(self):
        checkpoints = list(self._checkpoints.values())
        checkpoints.sort(key=lambda cpt: cpt["cpt_num"])

        # Drop excess elements
        while len(self._cpt_tbl) > len(checkpoints):
            del self._cpt_tbl[len(checkpoints) - 1]

        # Update existing rows
        for idx, cpt in enumerate(checkpoints[0 : len(self._cpt_tbl)]):
            self._cpt_tbl[idx] = cpt

        # Add new rows
        for cpt in checkpoints[len(self._cpt_tbl) :]:
            self._cpt_tbl.append(cpt)


class _CheckpointTable(Table):
    def __init__(self, parent, **kwargs):
        super(_CheckpointTable, self).__init__(
            parent,
            columns=(
                ("cpt_type", "Type"),
                ("cpt_order", "Order"),
            ),
            **kwargs
        )

    def _getobject(self, checkpoint):
        return (
            "%d. %s" % (checkpoint["cpt_type"], checkpoint["loc_id"]),
            (
                checkpoint["cpt_type"],
                checkpoint["cpt_order"],
            ),
            checkpoint,
        )


# .------------------------------- New Checkpoint --------------------------.
# |       .-----.          .------------------------------------------.---. |
# | Nbr.  |     | Location |                                          | v | |
# |       '-----'          '------------------------------------------'---' |
# |       .-----.          .------------------------------------------.---. |
# | Order |     |    Type  |                                          | v | |
# |       '-----'          '------------------------------------------'---' |
# | .-----------------------------------. .-------------------------------. |
# | |             COMMIT                | |              CLOSE            | |
# | '-----------------------------------' '-------------------------------' |
# '-------------------------------------------------------------------------'
class _LocationEditDialogue(object):
    @classmethod
    def show(cls, parent, location, **kwargs):
        tl = tkinter.Toplevel(parent)
        dlg = cls(parent=tl, location=location, **kwargs)
        tl.transient(parent)  # dialog window is related to main
        tl.wait_visibility()  # can't grab until window appears, so we wait
        tl.grab_set()  # ensure all input goes to our window
        tl.wait_window()  # block until window is destroyed

        return dlg._committed

    def __init__(
        self,
        title,
        location,
        commit_label="COMMIT",
        close_label="CLOSE",
        parent=None,
    ):
        if parent is None:
            parent = tkinter.Tk()

        self._location = location
        self._log = location._log.getChild("ui")
        self._committed = None
        self._parent = parent
        self._parent.protocol("WM_DELETE_WINDOW", self._dismiss)

        self._window = ttk.Frame(self._parent)

        num_lbl = ttk.Label(self._window, text="Number")
        num_lbl.grid(column=0, row=0)
        self._num_var = tkinter.StringVar(value=location["loc_num"])
        self._num_ent = ttk.Entry(self._window, textvariable=self._num_var)
        self._num_ent.grid(column=1, row=0, sticky=(tkinter.W, tkinter.E))

        name_lbl = ttk.Label(self._window, text="Name")
        name_lbl.grid(column=2, row=0)
        self._name_var = tkinter.StringVar(value=location["loc_name"])
        self._name_ent = ttk.Entry(self._window, textvariable=self._name_var)
        self._name_ent.grid(column=3, row=0, sticky=(tkinter.W, tkinter.E))

        tz_lbl = ttk.Label(self._window, text="Time-zone")
        tz_lbl.grid(column=0, row=1)
        self._tz_var = tkinter.StringVar(value=location["loc_tz"])
        self._tz_lst = ttk.Combobox(self._window, textvariable=self._tz_var)
        self._tz_lst.state(["readonly"])
        self._tz_lst["values"] = (
            "EVENT",
            "LOCAL",
        ) + tuple(sorted(zoneinfo.available_timezones()))
        self._tz_lst.grid(
            column=1,
            row=1,
            columnspan=3,
            rowspan=1,
            sticky=(tkinter.W, tkinter.E),
        )

        buttons = ButtonBox(parent=self._window)
        buttons.add_button(commit_label, command=self._commit)
        buttons.add_button(close_label, command=self._dismiss)
        buttons.grid(
            column=0,
            row=2,
            columnspan=4,
            rowspan=1,
            sticky=(tkinter.E, tkinter.W),
        )
        self._window.columnconfigure(1, weight=1)
        self._window.columnconfigure(3, weight=1)
        self._window.grid()
        self._parent.title(title)

    def _commit(self):
        try:
            self._location.uservalue["loc_num"] = self._num_var.get()
            self._location.uservalue["loc_name"] = self._name_var.get()
            self._location.uservalue["loc_tz"] = self._tz_var.get()
        except ValueError as e:
            messagebox.showerror(message=str(e))
            return

        self._committed = True
        self._close()

    def _dismiss(self):
        self._location.revert()
        self._committed = False
        self._close()

    def _close(self):
        self._parent.grab_release()
        self._parent.destroy()


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
    def __init__(self, event, parent=None):
        if parent is None:
            parent = tkinter.Tk()

        self._db = event.db
        self._event = event
        self._log = event._log.getChild("ui")
        self._locations = {}
        self._divisions = {}

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
        self._evttype_var = tkinter.StringVar(
            value=event["event_type"].data.name
        )
        self._evttype_lst = ttk.Combobox(
            self._evtsetup_frame, textvariable=self._evttype_var
        )
        self._evttype_lst.state(["readonly"])
        self._evttype_lst["values"] = tuple(
            et.data.name for et in EVENT_TYPES
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
        self._evtname_var = tkinter.StringVar(
            value=event.uservalue["auth_org"]
        )
        self._authorg_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._evtname_var
        )
        self._authorg_ent.grid(column=1, row=1, sticky=(tkinter.W, tkinter.E))

        location_lbl = ttk.Label(self._evtsetup_frame, text="Location")
        location_lbl.grid(column=2, row=1)
        self._evtname_var = tkinter.StringVar(
            value=event.uservalue["location"]
        )
        self._location_ent = ttk.Entry(
            self._evtsetup_frame, textvariable=self._evtname_var
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
        self._loc_tbl = _LocationTable(self._locations_frame)
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
        self._div_tbl = _DivisionTable(self._divisions_frame)
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

    def _commit(self):
        pass

    def _dismiss(self):
        pass

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
        result = _LocationEditDialogue.show(
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

        result = _LocationEditDialogue.show(
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
        result = _DivisionEditDialogue.show(
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

        result = _DivisionEditDialogue.show(
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
        result = _DivisionEditDialogue.show(
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

        result = _DivisionEditDialogue.show(
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


if __name__ == "__main__":
    import logging
    import datetime
    from .model.db import Database

    logging.basicConfig(level=logging.DEBUG)

    db = Database("test.sqlite3")
    db.init()

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
