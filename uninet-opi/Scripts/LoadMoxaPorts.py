from org.csstudio.display.builder.runtime.script import ScriptUtil
from org.csstudio.display.builder.model import WidgetFactory

logger = ScriptUtil.getLogger()
macros = widget.getEffectiveMacros()
prefix = macros.getValue("P")
port_count = macros.getValue("NPORTS")

try:
    port_count = int(port_count)
except:
    ScriptUtil.showMessageDialog(widget, "Moxa port count is missing; open this display from the Moxa array")
    port_count = 0

template_widget = ScriptUtil.findWidgetByName(widget, "element_template")
row_width = template_widget.getPropertyValue("width")
row_height = template_widget.getPropertyValue("height")
children = widget.runtimeChildren()
for child in list(children.getValue()):
    if str(child.getPropertyValue("name")).startswith("Instance_MoxaPort_"):
        children.removeChild(child)

for port_number in range(1, port_count + 1):
    row = WidgetFactory.getInstance().getWidgetDescriptor("embedded").createWidget()
    row.setPropertyValue("name", "Instance_MoxaPort_" + str(port_number))
    row.setPropertyValue("x", 0)
    row.setPropertyValue("y", 24 + (port_number - 1) * row_height)
    row.setPropertyValue("width", row_width)
    row.setPropertyValue("height", row_height)
    row.getPropertyValue("macros").add("P", prefix)
    row.getPropertyValue("macros").add("N", str(port_number))
    row.setPropertyValue("file", "moxaPortSummary.bob")
    children.addChild(row)

logger.info("Loaded " + str(port_count) + " Moxa serial ports for " + str(prefix))
