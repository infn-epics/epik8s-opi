from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
import epik8sutil
from org.phoebus.pv import PVPool
#pvs = ScriptUtil.getPVs(widget)
selection=PVUtil.getLong(pvs[0])

cnt=0
if selection:
    print "**** Selecting all "+str(len(pvs))
else:
    print "**** DEselecting all "+str(len(pvs))
pvs[1].write(0)

# This checkbox lives outside the Selection group, so it can't see the
# ZONE/TYPE/FUNC macros directly. $(DID) resolves consistently across embed
# boundaries when substituted in a pv_name string (same mechanism used by
# mag_display.bob's population script, which is why the displayed list
# already filters correctly) - so these are declared directly as extra
# non-triggering pv_names on this widget's script in mag_array.bob, rather
# than resolved imperatively (getEffectiveMacros().getValue("DID") returns
# None) or looked up via findWidgetByName (doesn't cross into the sibling
# Selection group in mag_dynamic.bob).
zoneSel = PVUtil.getString(pvs[2])
typeSel = PVUtil.getString(pvs[3])
funcSel = PVUtil.getString(pvs[4])
print "**** DEBUG zoneSel=" + repr(zoneSel) + " typeSel=" + repr(typeSel) + " funcSel=" + repr(funcSel)

devarray = epik8sutil.conf_to_dev(widget, zoneSel, typeSel, funcSel)
print "**** DEBUG devarray has " + str(len(devarray)) + " devices"
names=[]
for i in range(len(devarray)):
    n=devarray[i]['P']+":"+devarray[i]['R']
    names.append(n)
print "**** DEBUG names=" + repr(names)

pvrl=PVPool.getPVReferences()
for pvr in pvrl:
    entry=pvr.getEntry()
    name=entry.getName()
    if name.startswith("loc://selection:"):
        entry.write(0)
        if selection:
            for sel in names:
                if sel in name:
                    entry.write(1)
                    print "* selecting "+sel
                    cnt+=1

pvs[1].write(cnt)
