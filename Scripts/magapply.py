from org.csstudio.display.builder.runtime.script import PVUtil
import time

# Pushes a set of magnet power supplies to their desired state and current, used by the pretune
# steps and by the restore display.
#
# A power supply cannot take a current before it is in the desired state, so it is done in two steps:
#   1. STATE: for every device whose state is not the desired one
#        - ON -> OFF/STANDBY: CURRENT_SP is first set to 0 and the state is changed only once
#          |CURRENT_RB| <= zero_tolerance (waited up to `timeout`)
#        - write STATE_SP and wait (all devices together, up to `timeout`) until STATE_RB reaches it
#   2. CURRENT: only for the devices whose state has been reached and has to be ON, write
#      CURRENT_SP and wait (all together, up to `timeout`) until CURRENT_RB is within tolerance.
#      The current of a device that has to be OFF/STANDBY is not meaningful and is not written.
# Devices that do not complete a step in time are reported: use retry=True to redo them.

# States that can be commanded via STATE_SP, anything else (INTERLOCK, FAULT ...) is skipped
RESTORABLE_STATES = {"ON", "STANDBY", "OFF"}
OFF_STATES = ("OFF", "STANDBY")

DEFAULT_TIMEOUT_S = 30.0
DEFAULT_ZERO_TOLERANCE = 0.5
POLL_S = 0.2
CURRENT_EPSILON = 0.001


def read_positive(pvname, default):
    """Value of a local PV of the display, `default` if missing or not positive."""
    try:
        value = PVUtil.getDouble(PVUtil.createPV(pvname, 10))
        if value > 0:
            print("READ " + pvname + " = " + str(value))
            return value
        print("## " + pvname + " = " + str(value) + " not positive, using default " + str(default))
    except Exception as e:
        print("## Cannot read " + pvname + " (" + str(e) + "), using default " + str(default))
    return default


def read_timeout(pvname):
    return read_positive(pvname, DEFAULT_TIMEOUT_S)


def read_zero_tolerance(pvname):
    return read_positive(pvname, DEFAULT_ZERO_TOLERANCE)


def state_reached(desired, actual):
    """No (restorable) desired state: nothing to reach. STANDBY counts as OFF."""
    if desired not in RESTORABLE_STATES:
        return True
    if desired in OFF_STATES:
        return actual in OFF_STATES
    return actual == desired


def current_reached(desired_state, desired, readback, tolerance):
    """The current of a device that has to be OFF is not meaningful."""
    if desired_state in OFF_STATES:
        return True
    return abs(desired - readback) <= tolerance


def apply(devices, tolerance=0.1, retry=False, force_current=False, timeout=DEFAULT_TIMEOUT_S,
          set_current=True, zero_tolerance=DEFAULT_ZERO_TOLERANCE):
    """devices: list of {"base": "P:R", "current": float, "state": str}.

    retry          : leave alone the devices that already reached state and current (within tolerance)
    force_current  : write CURRENT_SP even if it already holds the wanted value
    timeout        : seconds allowed to each wait (current to 0, state, current)
    zero_tolerance : |CURRENT_RB| considered zero, before switching an ON device OFF/STANDBY
    set_current    : False = step 1 (states) only

    Returns {"applied": [base], "unchanged": [base], "zero_timeout": [base], "state_timeout": [base],
             "current_timeout": [base], "errors": [str], "readback": {base: str}, "timeout": timeout,
             "zero_tolerance": zero_tolerance}."""
    pvcache = {}

    def pv(name):
        if name not in pvcache:
            pvcache[name] = PVUtil.createPV(name, 500)
        return pvcache[name]

    def read_state(base):
        return str(pv(base + ":STATE_RB").read().getValue())

    def read_current(base):
        return float(pv(base + ":CURRENT_RB").read().getValue())

    def wait(items, done):
        """Polls done(item) for all items together, up to timeout. Returns the items not done."""
        deadline = time.time() + timeout
        while items and time.time() < deadline:
            time.sleep(POLL_S)
            still = []
            for item in items:
                try:
                    if not done(item):
                        still.append(item)
                except Exception as e:
                    failed.add(item["base"])
                    result["errors"].append(item["base"] + ": " + str(e))
            items = still
        return items

    result = {"applied": [], "unchanged": [], "zero_timeout": [], "state_timeout": [],
              "current_timeout": [], "errors": [], "readback": {}, "timeout": timeout,
              "zero_tolerance": zero_tolerance}
    failed = set()
    print("SETTINGS tolerance=" + str(tolerance) + " zero_tolerance=" + str(zero_tolerance) +
          " timeout=" + str(timeout) + " retry=" + str(retry))

    todo = []
    for d in devices:
        base = d["base"]
        try:
            actual = read_state(base)
            state_ok = state_reached(d["state"], actual)
            if retry:
                if state_ok and current_reached(d["state"], d["current"], read_current(base), tolerance):
                    result["unchanged"].append(base)
                    continue
            todo.append({"base": base, "current": d["current"], "state": d["state"],
                         "actual": actual, "state_ok": state_ok})
        except Exception as e:
            result["errors"].append(base + ": " + str(e))

    ## 1a. ON -> OFF/STANDBY: current to zero before changing the state
    zeroing = [d for d in todo if not d["state_ok"] and d["actual"] == "ON" and d["state"] in OFF_STATES]
    for d in list(zeroing):
        try:
            pv(d["base"] + ":CURRENT_SP").write(0.0)
            print("ZERO " + d["base"] + ":CURRENT_SP = 0 before " + d["state"])
        except Exception as e:
            zeroing.remove(d)
            failed.add(d["base"])
            result["errors"].append(d["base"] + ": " + str(e))
    not_zero = set(d["base"] for d in wait(zeroing, lambda d: abs(read_current(d["base"])) <= zero_tolerance))

    ## 1b. states
    waiting = []
    for d in todo:
        base = d["base"]
        if d["state_ok"] or base in failed:
            continue
        if base in not_zero:
            ## never switch off a supply still delivering current
            result["zero_timeout"].append(base)
            continue
        try:
            pv(base + ":STATE_SP").write(d["state"])
            print("APPLY " + base + ":STATE_SP = " + d["state"])
            waiting.append(d)
        except Exception as e:
            failed.add(base)
            result["errors"].append(base + ": " + str(e))
    stuck = set(d["base"] for d in wait(waiting, lambda d: state_reached(d["state"], read_state(d["base"]))))

    ## 2. currents, only where the state has been reached
    ramping = []
    for d in todo:
        base = d["base"]
        if base in failed or base in not_zero:
            continue
        if base in stuck:
            result["state_timeout"].append(base)
            continue
        if not set_current or d["state"] in OFF_STATES:
            result["applied"].append(base)
            continue
        try:
            actual_sp = float(pv(base + ":CURRENT_SP").read().getValue())
            if force_current or abs(d["current"] - actual_sp) > CURRENT_EPSILON:
                pv(base + ":CURRENT_SP").write(d["current"])
                print("APPLY " + base + ":CURRENT_SP = " + str(d["current"]))
            ramping.append(d)
        except Exception as e:
            failed.add(base)
            result["errors"].append(base + ": " + str(e))
    slow = set(d["base"] for d in wait(ramping, lambda d: abs(d["current"] - read_current(d["base"])) <= tolerance))

    for d in ramping:
        base = d["base"]
        if base in failed:
            continue
        if base in slow:
            result["current_timeout"].append(base)
        else:
            result["applied"].append(base)

    ## actual readbacks of what did not complete, shown by summary()
    for base in result["zero_timeout"] + result["state_timeout"] + result["current_timeout"]:
        try:
            result["readback"][base] = ("STATE_RB=" + read_state(base) +
                                        " CURRENT_RB=%.3f" % read_current(base))
        except Exception as e:
            result["readback"][base] = str(e)

    return result


def incomplete(result):
    """True if some device did not complete the procedure."""
    return bool(result["zero_timeout"] or result["state_timeout"] or result["current_timeout"]
                or result["errors"])


def _names(bases, readback=None):
    if readback:
        text = "\n".join(b + "  (" + readback.get(b, "?") + ")" for b in bases[:10])
    else:
        text = ", ".join(bases[:10])
    if len(bases) > 10:
        text += ", ... (" + str(len(bases)) + " in total)"
    return text


def summary(result, total):
    """Text for a message dialog."""
    secs = str(int(result.get("timeout", DEFAULT_TIMEOUT_S))) + " s"
    msg = "Completed on " + str(len(result["applied"])) + " of " + str(total) + " devices."
    if result["unchanged"]:
        msg += "\n" + str(len(result["unchanged"])) + " already at their target."
    if result["zero_timeout"]:
        msg += ("\n\n|CURRENT_RB| NOT <= zero tolerance (" + str(result.get("zero_tolerance")) + " A) in "
                + secs + ", NOT switched off (use Retry):\n"
                + _names(result["zero_timeout"], result.get("readback")))
    if result["state_timeout"]:
        msg += ("\n\nState NOT reached within " + secs + ", current NOT set (use Retry):\n"
                + _names(result["state_timeout"], result.get("readback")))
    if result["current_timeout"]:
        msg += ("\n\nCurrent NOT within tolerance within " + secs + " (use Retry):\n"
                + _names(result["current_timeout"], result.get("readback")))
    if result["errors"]:
        msg += "\n\nErrors:\n" + "\n".join(result["errors"][:10])
    return msg
