from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil

import epik8sutil

import os
from java.lang import Exception
logger = ScriptUtil.getLogger()

# zoneSelector = widget.getEffectiveMacros().getValue("ZONE")
# typeSelector = widget.getEffectiveMacros().getValue("TYPE")
# devgroup_widget=widget.getEffectiveMacros().getValue("GROUP")
wtemplate = ScriptUtil.findWidgetByName(widget, "element_template") ## name of the hidden template
# conffile = widget.getEffectiveMacros().getValue("CONFFILE")
# display_model = widget.getDisplayModel()
# display_path = os.path.dirname(display_model.getUserData(display_model.USER_DATA_INPUT_FILE))

# if conffile is None:
#     ScriptUtil.showMessageDialog(widget, "## Please set CONFFILE macro to a correct YAML configuration file")
#     exit()
# confpath = display_path + "/" + conffile

visible_pv = pvs[3] if len(pvs) > 4 and widget.getEffectiveMacros().getValue("GROUP") == "mag" else None
visible_filters_pv = pvs[4] if visible_pv is not None else None
if visible_pv is not None:
    visible_pv.write("")
    visible_filters_pv.write("")
devarray = epik8sutil.conf_to_dev(widget)

offset = 5
embedded_width  = wtemplate.getPropertyValue("width")
embedded_height = wtemplate.getPropertyValue("height") + offset
devgroup_widget=widget.getEffectiveMacros().getValue("GROUP")
bobitem=widget.getEffectiveMacros().getValue("BOBITEM")
if bobitem is None:
   bobitem=devgroup_widget+ "_channel.bob"
display = widget.getDisplayModel()
# Remove all existing runtime children first
children_prop = widget.runtimeChildren()
for child in list(children_prop.getValue()):
    if child.getPropertyValue("name").startswith("Instance_" + devgroup_widget):
        children_prop.removeChild(child)


for i in range(len(devarray)):
    x = 0
    y = i * embedded_height
    instance = epik8sutil.createInstance(embedded_width,embedded_height,devgroup_widget+str(i),bobitem,x, y, devarray[i])
    widget.runtimeChildren().addChild(instance)

if visible_pv is not None:
    visible_pv.write("\n".join(d['P'] + ':' + d['R'] for d in devarray))
    visible_filters_pv.write("\t".join((PVUtil.getString(pvs[0]),
                                         PVUtil.getString(pvs[1]),
                                         PVUtil.getString(pvs[2]))))
