from org.csstudio.display.builder.runtime.script import PVUtil


def visible_bases(widget, did):
    """Exact PV bases published by the source magnet window after filtering."""
    if not did or did == '0' or '$' in did:
        raise ValueError('Cannot identify the source magnet window')
    try:
        zone = PVUtil.getString(PVUtil.createPV('loc://ZONE_' + did, 10))
        kind = PVUtil.getString(PVUtil.createPV('loc://FUNC_' + did, 10))
        model = PVUtil.getString(PVUtil.createPV('loc://TYPE_' + did, 10))
        snapshot = PVUtil.getString(PVUtil.createPV('loc://mag-visible-' + did, 10))
        signature = PVUtil.getString(PVUtil.createPV('loc://mag-visible-filters-' + did, 10))
    except Exception as error:
        raise ValueError('Cannot read the source magnet filters: ' + str(error))
    if not zone or not kind or not model or not snapshot or not signature:
        raise ValueError('Source magnet selection is unavailable; wait for the magnet view to finish loading')
    if tuple(signature.split('\t')) != (zone, kind, model):
        raise ValueError('Source magnet filters are still updating; retry after the list refreshes')
    bases = [base for base in snapshot.split('\n') if base]
    if any(':' not in base for base in bases):
        raise ValueError('Source magnet list is invalid')
    return set(bases)


def skipped_message(skipped, label):
    if not skipped:
        return ''
    names = ', '.join(skipped[:10])
    if len(skipped) > 10:
        names += ', ...'
    return str(len(skipped)) + ' ' + label + ' magnet(s) will not be applied because they are outside the source magnet window\'s Zone, Type or Model selection:\n' + names
