#!/usr/bin/env python3
# KC2 / K10Plus IR -> keyboard/mouse helper.
#   MOUSE-KEY       = toggle cursor mode: directions = pointer move,
#                     OK = middle click
#   HOME key        = Ctrl+C
#   MENU / BACK / others = pass through unchanged (menu behaves like the
#                     keyboard menu key, back arrives as KEY_ESC from the
#                     keymap)
# The source device is grabbed and everything not intercepted is re-injected
# untouched.
import evdev
from evdev import ecodes as E

SRC_NAME = "gpio_ir_recv"
STEP = 16  # px per repeat tick


def find_src():
    for p in evdev.list_devices():
        try:
            d = evdev.InputDevice(p)
            if d.name == SRC_NAME:
                return d
        except OSError:
            continue
    raise SystemExit("rc device %r not found" % SRC_NAME)


src = find_src()
caps = {t: list(cs) for t, cs in src.capabilities().items() if t != E.EV_SYN}
caps.setdefault(E.EV_KEY, []).extend([E.BTN_RIGHT, E.BTN_MIDDLE, E.KEY_LEFTCTRL, E.KEY_C])
caps[E.EV_KEY] = sorted(set(caps[E.EV_KEY]))
ui = evdev.UInput(events=caps, name="kc2ir-mouse")
src.grab()

mouse_mode = False


def key(code, val):
    ui.write(E.EV_KEY, code, val)
    ui.syn()


for ev in src.read_loop():
    if ev.type == E.EV_SYN:
        ui.syn()
        continue
    if ev.type == E.EV_KEY:
        if ev.code == E.KEY_HOME:  # Ctrl+C combo, repeats ignored
            if ev.value == 1:
                key(E.KEY_LEFTCTRL, 1); key(E.KEY_C, 1)
            elif ev.value == 0:
                key(E.KEY_C, 0); key(E.KEY_LEFTCTRL, 0)
            continue
        if ev.code == E.KEY_CONTEXT_MENU and ev.value == 1:
            mouse_mode = not mouse_mode
            continue
        if mouse_mode:
            if ev.code == E.KEY_UP and ev.value:
                ui.write(E.EV_REL, E.REL_Y, -STEP); ui.syn(); continue
            if ev.code == E.KEY_DOWN and ev.value:
                ui.write(E.EV_REL, E.REL_Y, STEP); ui.syn(); continue
            if ev.code == E.KEY_LEFT and ev.value:
                ui.write(E.EV_REL, E.REL_X, -STEP); ui.syn(); continue
            if ev.code == E.KEY_RIGHT and ev.value:
                ui.write(E.EV_REL, E.REL_X, STEP); ui.syn(); continue
            if ev.code == E.KEY_ENTER:
                if ev.value == 1:
                    key(E.BTN_MIDDLE, 1)
                elif ev.value == 0:
                    key(E.BTN_MIDDLE, 0)
                continue
            # BACK etc pass through below
    ui.write(ev.type, ev.code, ev.value)
