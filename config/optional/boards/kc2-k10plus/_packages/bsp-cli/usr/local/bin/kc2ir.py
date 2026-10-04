#!/usr/bin/env python3
# KC2 / K10Plus IR -> mouse helper.
#   MENU key        = right click (always)
#   MOUSE-KEY       = toggle cursor mode: directions = pointer move,
#                     OK = middle click; BACK/power/etc pass through
# Everything not intercepted is re-injected untouched. The source device is
# grabbed so the desktop only sees our clean re-injected stream.
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
caps.setdefault(E.EV_REL, []).extend([E.REL_X, E.REL_Y])
caps.setdefault(E.EV_KEY, []).extend([E.BTN_RIGHT, E.BTN_MIDDLE])
caps[E.EV_REL] = sorted(set(caps[E.EV_REL]))
caps[E.EV_KEY] = sorted(set(caps[E.EV_KEY]))
ui = evdev.UInput(events=caps, name="kc2ir-mouse")
src.grab()

mouse_mode = False
for ev in src.read_loop():
    if ev.type == E.EV_SYN:
        ui.syn()
        continue
    if ev.type == E.EV_KEY:
        if ev.code == E.KEY_MENU:  # right click, repeats ignored
            if ev.value == 1:
                ui.write(E.EV_KEY, E.BTN_RIGHT, 1); ui.syn()
            elif ev.value == 0:
                ui.write(E.EV_KEY, E.BTN_RIGHT, 0); ui.syn()
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
                    ui.write(E.EV_KEY, E.BTN_MIDDLE, 1); ui.syn()
                elif ev.value == 0:
                    ui.write(E.EV_KEY, E.BTN_MIDDLE, 0); ui.syn()
                continue
            # BACK etc pass through below
    ui.write(ev.type, ev.code, ev.value)
