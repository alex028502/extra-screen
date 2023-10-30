import subprocess
import sys
import os
import tempfile

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio

__dir__ = os.path.dirname(os.path.abspath(__file__))


def debug(*args):
    if os.isatty(0):
        print(*args)


session_name = sys.argv[1]

# These are the only special cases I have needed so far, but you will surely
# discover others that you need. I made these the same as what the terminal
# emulator produces.  However, I think there is no reason you couldn't just
# start your screen session with whichever TERM you want, and make these match
# since we are not using the tablet keyboard.  For example, you could start
# screen with TERM=ansi and then send ^H instead of ^? for backspace. I think
# it will work as long as screen is started with the TERM variable that matches
# the values in this table, because I think (hope) that screen will then
# translate all incoming signals to the TERM=screen from whatever you language
# you told it you were going to speak to it.

SPECIAL_CASES = {
    "Up": "\x1b[A",
    "Down": "\x1b[B",
    "Right": "\x1b[C",
    "Left": "\x1b[D",
    "Home": "\x1b[H",
    "End": "\x1b[F",
    "Page_Up": "\x1b[5~",
    "Page_Down": "\x1b[6~",
    "BackSpace": "\x7f",
    "Delete": "\x1b\x5b\x33\x7e",
}


# Some terminal emulators send ascii 'delete' for the backspace key and others
# send ascii 'backspace' for the backspace key. None of them send ascii
# `backspace' or ascii 'delete' for the 'delete' key.


def interpret(event):
    # lots of named key events have a pretty simple relationship with key codes
    if Gdk.keyval_name(event.keyval) in SPECIAL_CASES:
        return SPECIAL_CASES[Gdk.keyval_name(event.keyval)]

    # When you hold down Alt, the terminal emulator just sticks escape in front
    # of everything.
    if event.state & Gdk.ModifierType.MOD1_MASK:
        return "\x1b" + event.string

    if event.string == "\\":
        return "\\\\"

    if event.string == "^":
        return "\\^"

    return event.string


def on_drag_data_received(widget, drag_context, x, y, data, info, time):
    uris = data.get_uris()
    if uris:
        for uri in uris:
            debug("uri %s" % uri)
            file = Gio.File.new_for_uri(uri)
            file_path = file.get_path()
            debug("file path: " + file_path)
            subprocess.run(["screen", "-S", session_name, "-X", "stuff", file_path])


def key_press_event(widget, event):
    key = Gdk.keyval_name(event.keyval)
    debug("---------")
    debug("pressed %s (%s)" % (key, len(event.string)))

    message = interpret(event)

    debug("message len", len(message))
    debug("string len", len(event.string))
    for i in event.string:
        debug("char: %s" % ord(i))
    for attr in dir(event):
        if not attr.startswith("__"):
            debug(f"{attr}: {getattr(event, attr)}")

    if key == "V" and (event.state & Gdk.ModifierType.CONTROL_MASK):
        debug("paste!!!")
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clip_text = clipboard.wait_for_text()
        if clip_text:
            # from man screen
            # > You cannot paste large buffers with the stuff command. It is
            # most useful for key bindings.
            # but actually it worked pretty well - the problem that made me
            # stop using stuff here is that screen seems to expand whatever you
            # give it as if it were in single quotes and I couldn't figure out
            # a way to escape it to exactly that level
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(clip_text.encode())
            subprocess.run(
                ["screen", "-S", session_name, "-X", "readbuf", tmp_file.name]
            )
            subprocess.run(["screen", "-S", session_name, "-X", "paste", "."])
            os.unlink(tmp_file.name)
        return

    # this case is so special it doesn't even fit into special cases
    # '\x00' doesn't work the other way because of the 'embedded null byte'
    # this is a bit clunky and puts a message about slurping in the terminal
    # screen, but it is just for copying the odd thing with tmux (or emacs)
    # so it works OK
    if event.keyval == Gdk.KEY_space and (event.state & Gdk.ModifierType.CONTROL_MASK):
        debug("special event")
        subprocess.run(
            ["screen", "-S", session_name, "-X", "readbuf", __dir__ + "/ctrl-space.bin"]
        )
        subprocess.run(["screen", "-S", session_name, "-X", "paste", "."])
        return

    subprocess.run(
        ["screen", "-S", session_name, "-X", "stuff", message],
    )


win = Gtk.Window()
win.connect("destroy", Gtk.main_quit)
image_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
    "./picture.png",
    96,
    96,
    True,
)
image = Gtk.Image()
image.set_from_pixbuf(image_pixbuf)
win.add(image)

win.set_title("\U0001F4BB")
win.connect("key-press-event", key_press_event)
win.set_icon_from_file("./icon.png")
win.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
win.drag_dest_add_uri_targets()
win.connect("drag-data-received", on_drag_data_received)
win.show_all()
Gtk.main()
