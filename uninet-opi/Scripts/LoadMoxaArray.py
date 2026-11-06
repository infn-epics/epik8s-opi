from org.csstudio.display.builder.runtime.script import ScriptUtil
from org.csstudio.display.builder.model import WidgetFactory
from org.yaml.snakeyaml import Yaml
from java.io import FileReader

import epik8sutil
import os

logger = ScriptUtil.getLogger()
macros = widget.getEffectiveMacros()
conffile = macros.getValue("CONFFILE")
if conffile is None:
    ScriptUtil.showMessageDialog(widget, "Please set the CONFFILE macro to a values YAML file")
else:
    display_model = widget.getDisplayModel()
    display_path = os.path.dirname(display_model.getUserData(display_model.USER_DATA_INPUT_FILE))
    confpath = os.path.normpath(os.path.join(display_path, conffile))

    # The array may be embedded in a top-level OPI, so resolve the same relative
    # CONFFILE from its parent displays when it is not next to this display.
    if not os.path.exists(confpath):
        search_dir = display_path
        for _ in range(5):
            search_dir = os.path.dirname(search_dir)
            if not search_dir:
                break
            candidate = os.path.normpath(os.path.join(search_dir, conffile))
            if os.path.exists(candidate):
                confpath = candidate
                break

    if not os.path.exists(confpath):
        ScriptUtil.showMessageDialog(widget, "Cannot find values file: " + confpath)
    else:
        # values.yaml normally merges every values-*.yaml in conf_to_iocs.
        # Moxa views represent one area, so read only the selected file.
        data = Yaml().load(FileReader(confpath))
        epics_config = data.get("epicsConfiguration") if data is not None else None
        ioc_map = epics_config.get("iocs") if epics_config is not None else None
        iocs = list(ioc_map.values()) if ioc_map is not None else []
        if os.path.basename(confpath) != "values.yaml":
            # A serial server can serve more than one area. Shared Moxa IOCs
            # are defined once in values.yaml; show those used by this file.
            used_servers = set(str(ioc.get("server")) for ioc in iocs
                               if ioc.get("server") is not None)
            defined_servers = set(str(ioc.get("server")) for ioc in iocs
                                  if str(ioc.get("template") or ioc.get("devtype") or "").lower() == "moxanport")
            basepath = os.path.join(os.path.dirname(confpath), "values.yaml")
            if os.path.exists(basepath):
                base_data = Yaml().load(FileReader(basepath))
                base_config = base_data.get("epicsConfiguration") if base_data is not None else None
                base_iocs = base_config.get("iocs") if base_config is not None else None
                if base_iocs is not None:
                    for ioc in base_iocs.values():
                        server = str(ioc.get("server") or "")
                        template = str(ioc.get("template") or ioc.get("devtype") or "")
                        if template.lower() == "moxanport" and server in used_servers and server not in defined_servers:
                            iocs.append(ioc)
                            defined_servers.add(server)
        moxa_iocs = []
        for ioc in iocs:
            template = str(ioc.get("template") or ioc.get("devtype") or "")
            if template.lower() != "moxanport":
                continue
            if str(ioc.get("disable", False)).lower() == "true":
                continue
            name = str(ioc.get("name") or "")
            prefix = str(ioc.get("iocprefix") or "")
            if not name or not prefix:
                continue
            moxa_iocs.append({
                "NAME": name,
                "P": prefix,
                "SERVER": str(ioc.get("server") or ""),
                "NPORTS": str(ioc.get("nports") or "")
            })

        moxa_iocs.sort(key=lambda item: item["NAME"].lower())
        template_widget = ScriptUtil.findWidgetByName(widget, "element_template")
        row_width = template_widget.getPropertyValue("width")
        row_height = template_widget.getPropertyValue("height")
        children = widget.runtimeChildren()
        for child in list(children.getValue()):
            if str(child.getPropertyValue("name")).startswith("Instance_MoxaNPort_"):
                children.removeChild(child)

        for index, item in enumerate(moxa_iocs):
            row = epik8sutil.createInstance(
                row_width,
                row_height,
                "MoxaNPort_" + item["NAME"],
                "moxa/moxa_channel.bob",
                0,
                72 + index * row_height,
                item
            )
            children.addChild(row)

        logger.info("Loaded " + str(len(moxa_iocs)) + " Moxa NPorts from " + confpath)
