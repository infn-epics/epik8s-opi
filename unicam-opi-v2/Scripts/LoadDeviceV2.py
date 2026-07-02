"""
LoadDeviceV2.py - Load camera devices from YAML configuration for CameraV2 display.

This script reads the CONFFILE YAML configuration and populates the DeviceCombo
with available camera devices. It extracts the plugin enable flags for dynamic
interface configuration.
"""

from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from java.io import FileReader
from org.yaml.snakeyaml import Yaml
import os

logger = ScriptUtil.getLogger()

def get_camera_iocs_from_config(confpath, mywidget, devgroup="cam"):
    """
    Load camera IOC configurations from the YAML file.
    Returns a list of camera IOC configurations with their enable flags.
    """
    cameras = []
    
    if not os.path.exists(confpath):
        ScriptUtil.showMessageDialog(mywidget, "Cannot find file \"" + confpath + "\" - please set CONFFILE macro")
        return cameras
    
    yaml = Yaml()
    data = yaml.load(FileReader(confpath))
    epics_config = data.get("epicsConfiguration")
    
    if epics_config is None:
        ScriptUtil.showMessageDialog(mywidget, "Cannot find 'epicsConfiguration' in \"" + confpath + "\"")
        return cameras
    
    iocs = epics_config.get("iocs")
    if iocs is None:
        ScriptUtil.showMessageDialog(mywidget, "Cannot find iocs section in configuration file")
        return cameras
    
    for ioc in iocs:
        ioc_devgroup = ioc.get("devgroup", "")
        
        # Filter by camera device group
        if ioc_devgroup != devgroup:
            continue
        
        ioc_name = ioc.get("name", "")
        iocprefix = ioc.get("iocprefix", "")
        template = ioc.get("template", "")
        
        # Get enable flags from IOC config or iocparam
        roi_enable = ioc.get("roi_enable", False)
        proc_enable = ioc.get("proc_enable", False)
        stats_enable = ioc.get("stats_enable", False)
        overlay_enable = ioc.get("overlay_enable", False)
        tiff_enable = ioc.get("tiff_enable", True)
        stream_enable = ioc.get("stream_enable", False)
        
        # Override with iocparam if present
        iocparam = ioc.get("iocparam", [])
        for param in iocparam:
            pname = param.get("name", "")
            pvalue = param.get("value", False)
            if pname == "roi_enable":
                roi_enable = pvalue
            elif pname == "proc_enable":
                proc_enable = pvalue
            elif pname == "stats_enable":
                stats_enable = pvalue
            elif pname == "overlay_enable":
                overlay_enable = pvalue
            elif pname == "tiff_enable":
                tiff_enable = pvalue
            elif pname == "stream_enable":
                stream_enable = pvalue
        
        # Get devices for this IOC
        devices = ioc.get("devices", [])
        
        for dev in devices:
            dev_name = dev.get("name", "")
            dev_alias = dev.get("alias", dev_name)
            
            camera_config = {
                "NAME": dev_alias if dev_alias else dev_name,
                "IOC": ioc_name,
                "P": iocprefix,
                "R": dev_name,
                "TEMPLATE": template,
                "ROI_ENABLED": "1" if roi_enable else "0",
                "PROC_ENABLED": "1" if proc_enable else "0",
                "STATS_ENABLED": "1" if stats_enable else "0",
                "OVERLAY_ENABLED": "1" if overlay_enable else "0",
                "TIFF_ENABLED": "1" if tiff_enable else "0",
                "STREAM_ENABLED": "1" if stream_enable else "0"
            }
            
            # Device-level overrides
            dev_iocparam = dev.get("iocparam", [])
            for param in dev_iocparam:
                pname = param.get("name", "")
                pvalue = param.get("value", False)
                if pname == "roi_enable":
                    camera_config["ROI_ENABLED"] = "1" if pvalue else "0"
                elif pname == "proc_enable":
                    camera_config["PROC_ENABLED"] = "1" if pvalue else "0"
                elif pname == "stats_enable":
                    camera_config["STATS_ENABLED"] = "1" if pvalue else "0"
                elif pname == "overlay_enable":
                    camera_config["OVERLAY_ENABLED"] = "1" if pvalue else "0"
                elif pname == "tiff_enable":
                    camera_config["TIFF_ENABLED"] = "1" if pvalue else "0"
                elif pname == "stream_enable":
                    camera_config["STREAM_ENABLED"] = "1" if pvalue else "0"
            
            cameras.append(camera_config)
            logger.info("Found camera: " + str(camera_config))
    
    return cameras


# Main script execution
try:
    combo = ScriptUtil.findWidgetByName(widget, "DeviceCombo")
    
    # Get configuration file path
    conffile = widget.getEffectiveMacros().getValue("CONFFILE")
    display_model = widget.getDisplayModel()
    display_path = os.path.dirname(display_model.getUserData(display_model.USER_DATA_INPUT_FILE))
    
    if conffile is None:
        ScriptUtil.showMessageDialog(widget, "Please set CONFFILE macro to a valid YAML configuration file")
    else:
        confpath = display_path + "/" + conffile
        logger.info("Loading camera configuration from: " + confpath)
        
        # Get device group filter (default to 'cam')
        devgroup = widget.getEffectiveMacros().getValue("GROUP")
        if devgroup is None:
            devgroup = "cam"
        
        # Load camera configurations
        camera_list = get_camera_iocs_from_config(confpath, widget, devgroup)
        
        # Store camera list in widget user data for later use
        widget.setUserData("CAMERA_LIST", camera_list)
        
        # Populate combo with camera names
        names = []
        for cam in camera_list:
            display_name = cam.get("P", "") + ":" + cam.get("R", "")
            names.append(display_name)
        
        combo.setItems(names)
        logger.info("Loaded " + str(len(names)) + " cameras into combo")
        
except Exception as e:
    logger.error("LoadDeviceV2 error: " + str(e))
