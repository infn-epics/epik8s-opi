from org.csstudio.display.builder.runtime.script import PVUtil
import json


def visible_bases(widget, did):
    """Exact PV bases published by the source magnet window after filtering."""
    if not did or did == '0' or '$' in did:
        raise ValueError('Cannot identify the source magnet window')
    try:
        zone = PVUtil.getString(PVUtil.createPV('loc://ZONE_' + did, 10))
        kind = PVUtil.getString(PVUtil.createPV('loc://FUNC_' + did, 10))
        model = PVUtil.getString(PVUtil.createPV('loc://TYPE_' + did, 10))
        snapshot = PVUtil.getString(PVUtil.createPV('loc://mag-visible-' + did, 10))
    except Exception as error:
        raise ValueError('Cannot read the source magnet filters: ' + str(error))
    if not zone or not kind or not model or not snapshot:
        raise ValueError('Source magnet selection is unavailable; wait for the magnet view to finish loading')
    try:
        data = json.loads(snapshot)
        if (data['zone'], data['type'], data['model']) != (zone, kind, model):
            raise ValueError('Source magnet filters are still updating; retry after the list refreshes')
        bases = data['bases']
        if not isinstance(bases, list) or any(':' not in base for base in bases):
            raise ValueError('Source magnet list is invalid')
        return set(bases)
    except (KeyError, TypeError) as error:
        raise ValueError('Source magnet list is invalid: ' + str(error))


def skipped_message(skipped, label):
    if not skipped:
        return ''
    names = ', '.join(skipped[:10])
    if len(skipped) > 10:
        names += ', ...'
    return str(len(skipped)) + ' ' + label + ' magnet(s) will not be applied because they are outside the source magnet window\'s Zone, Type or Model selection:\n' + names
