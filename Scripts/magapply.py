from org.csstudio.display.builder.runtime.script import PVUtil
import time

# Pushes a set of magnet power supplies to their desired state and current, used by the pretune
# steps and by the restore display.
#
# A power supply cannot take a current before it is in the desired state, so the order is:
#   1. write STATE_SP of every device whose state is not the desired one
#   2. wait (all devices together, up to STATE_TIMEOUT_S) until STATE_RB reaches it
#   3. write CURRENT_SP, only of the devices whose state has been reached
# Devices whose state is not reached in time do not get the current: use retry=True to redo them.

# States that can be commanded via STATE_SP, anything else (INTERLOCK, FAULT ...) is skipped
RESTORABLE_STATES = {"ON", "STANDBY", "OFF"}

STATE_TIMEOUT_S = 20.0
POLL_S = 0.2
CURRENT_EPSILON = 0.001


def state_reached(desired, actual):
    """No (restorable) desired state: nothing to reach. STANDBY counts as OFF."""
    if desired not in RESTORABLE_STATES:
        return True
    if desired == "OFF":
        return actual in ("OFF", "STANDBY")
    return actual == desired


def current_reached(desired_state, desired, readback, tolerance):
    """The current of a device that has to be OFF is not meaningful."""
    if desired_state == "OFF":
        return True
    return abs(desired - readback) <= tolerance


def apply(devices, tolerance=0.1, retry=False, force_current=False):
    """devices: list of {"base": "P:R", "current": float, "state": str}.

    retry          : leave alone the devices that already reached state and current (within tolerance)
    force_current  : write CURRENT_SP even if it already holds the wanted value

    Returns {"applied": [base], "unchanged": [base], "state_timeout": [base], "errors": [str]}."""
    pvcache = {}

    def pv(name):
        if name not in pvcache:
            pvcache[name] = PVUtil.createPV(name, 500)
        return pvcache[name]

    def read_state(base):
        return str(pv(base + ":STATE_RB").read().getValue())

    result = {"applied": [], "unchanged": [], "state_timeout": [], "errors": []}

    todo = []
    for d in devices:
        base = d["base"]
        try:
            state_ok = state_reached(d["state"], read_state(base))
            if retry:
                readback = float(pv(base + ":CURRENT_RB").read().getValue())
                if state_ok and current_reached(d["state"], d["current"], readback, tolerance):
                    result["unchanged"].append(base)
                    continue
            todo.append((d, state_ok))
        except Exception as e:
            result["errors"].append(base + ": " + str(e))

    ## 1. states
    waiting = []
    failed = set()
    for d, state_ok in todo:
        if state_ok:
            continue
        try:
            pv(d["base"] + ":STATE_SP").write(d["state"])
            waiting.append(d)
        except Exception as e:
            failed.add(d["base"])
            result["errors"].append(d["base"] + ": " + str(e))

    ## 2. wait for all of them together
    deadline = time.time() + STATE_TIMEOUT_S
    while waiting and time.time() < deadline:
        time.sleep(POLL_S)
        still = []
        for d in waiting:
            try:
                if not state_reached(d["state"], read_state(d["base"])):
                    still.append(d)
            except Exception as e:
                failed.add(d["base"])
                result["errors"].append(d["base"] + ": " + str(e))
        waiting = still
    stuck = set(d["base"] for d in waiting)

    ## 3. currents
    for d, state_ok in todo:
        base = d["base"]
        if base in failed:
            continue
        if base in stuck:
            result["state_timeout"].append(base)
            continue
        try:
            actual_sp = float(pv(base + ":CURRENT_SP").read().getValue())
            if force_current or abs(d["current"] - actual_sp) > CURRENT_EPSILON:
                pv(base + ":CURRENT_SP").write(d["current"])
            result["applied"].append(base)
        except Exception as e:
            result["errors"].append(base + ": " + str(e))

    return result


def summary(result, total):
    """Text for a message dialog."""
    msg = "Applied to " + str(len(result["applied"])) + " of " + str(total) + " devices."
    if result["unchanged"]:
        msg += "\n" + str(len(result["unchanged"])) + " already at their target."
    if result["state_timeout"]:
        msg += ("\n\nState NOT reached within " + str(int(STATE_TIMEOUT_S)) + " s, current NOT set (use Retry):\n"
                + ", ".join(result["state_timeout"][:10]))
        if len(result["state_timeout"]) > 10:
            msg += ", ... (" + str(len(result["state_timeout"])) + " in total)"
    if result["errors"]:
        msg += "\n\nErrors:\n" + "\n".join(result["errors"][:10])
    return msg
