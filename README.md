[Find this project on codeberg](https://codeberg.org/sjlongland/field-tracker)

As a result of Github's decision to force AI-generated issues with no opt-out,
I am migrating personal projects of mine to Codeberg.  The project at Github
will be archived.

----

# Work-in-progress field event tracker

This is a crude event tracking application for horse endurance rides, bicycle
rides and car rallies, intended for use by emergency communications groups who
may be running check-points for competitor safety.

The application is a stand-alone GUI application with minimal dependencies
(just Python 3.8 or later, with the standard library) to make deployment as
simple as possible.  It is single-user, with no support for packet radio or
web-based users, and is geared towards operation in the field as well as in
base.

It is developed for the events that
[Brisbane Area WICEN (Inc.)](https://www.brisbanewicen.org.au) assists in, and
is loosely based on their in-house developed tracking system (which exclusively
operates in base).

**This project is a work-in-progress.**  Hardly anything is actually working at
this point.

## Requirements

Python 3.8, compiled with `tkinter` and `sqlite3` modules. (Sorry Windows
XP/Vista users, maybe consider installing Linux?)

It is tested and developed on Linux with a X11 desktop.  Your mileage may vary
on other platforms, patches for those platforms will be accepted on the proviso
that they do not unnecessarily complicate maintenance or cause problems on
actively supported platforms.

## Installing

We aren't there yet.  _Likely_, it'll be a case of using `pip` to install it,
but we'll write those instructions when it's possible to install this package.

## Running the application

Again, there's not much there to run, but you can play around with some parts:

- Event set-up UI: `python3 -m fieldtracker.eventsetup`
