from org.csstudio.display.builder.runtime.script import PVUtil
import epik8sutil


def visible_bases(widget, did):
    """PV bases in the source mag_dynamic window's current Zone/Type/Model view.

    In mag_dynamic.bob the Type combo writes FUNC_ and the Model combo writes
    TYPE_. Read the source window's local PVs, not the child dialog's macros.
    Fail closed if the source selection cannot be read.
    """
    if not did or did == '0' or '$' in did:
        raise ValueError('Cannot identify the source magnet window')
    try:
        zone = PVUtil.getString(PVUtil.createPV('loc://ZONE_' + did, 10))
        kind = PVUtil.getString(PVUtil.createPV('loc://FUNC_' + did, 10))
        model = PVUtil.getString(PVUtil.createPV('loc://TYPE_' + did, 10))
    except Exception as error:
        raise ValueError('Cannot read the source magnet filters: ' + str(error))
    if not zone or not kind or not model:
        raise ValueError('Source magnet filters are unavailable')
    devices = epik8sutil.conf_to_dev(widget, zone, model, kind)
    return set(d['P'] + ':' + d['R'] for d in devices)


def skipped_message(skipped, label):
    if not skipped:
        return ''
    names = ', '.join(skipped[:10])
    if len(skipped) > 10:
        names += ', ...'
    return str(len(skipped)) + ' ' + label + ' magnet(s) will not be applied because they are outside the source magnet window\'s Zone, Type or Model selection:\n' + names
