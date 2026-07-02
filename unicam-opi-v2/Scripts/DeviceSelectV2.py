"""
DeviceSelectV2.py - Handle camera device selection for CameraV2 display.

This script is triggered when the user selects a camera from the DeviceCombo.
It sets all the necessary macros (DEVICE, CAM, and plugin enable flags) on the
embedded CameraV2_Main.bob display.
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
        return cameras
    
    yaml = Yaml()
    data = yaml.load(FileReader(confpath))
    epics_config = data.get("epicsConfiguration")
    
    if epics_config is None:
        return cameras
    
    iocs = epics_config.get("iocs")
    if iocs is None:
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
    
    return cameras


# Main script execution
try:
    pv_value = PVUtil.getString(pvs[0])
    
    if pv_value and pv_value != "":
        logger.info("DeviceSelectV2: Selected device: " + pv_value)
        
        # Get configuration file path
        conffile = widget.getEffectiveMacros().getValue("CONFFILE")
        display_model = widget.getDisplayModel()
        display_path = os.path.dirname(display_model.getUserData(display_model.USER_DATA_INPUT_FILE))
        
        if conffile is None:
            logger.error("CONFFILE macro not set")
        else:
            confpath = display_path + "/" + conffile
            
            # Get device group filter (default to 'cam')
            devgroup = widget.getEffectiveMacros().getValue("GROUP")
            if devgroup is None:
                devgroup = "cam"
            
            # Load camera configurations
            camera_list = get_camera_iocs_from_config(confpath, widget, devgroup)
            
            # Find selected camera
            selected_camera = None
            for cam in camera_list:
                display_name = cam.get("P", "") + ":" + cam.get("R", "")
                if display_name == pv_value:
                    selected_camera = cam
                    break
            
            if selected_camera:
                logger.info("Found camera config: " + str(selected_camera))
                
                # Clear file first to trigger reload
                widget.setPropertyValue("file", "")
                
                # Set all macros on the embedded display
                macros = widget.getPropertyValue("macros")
                
                # Core PV macros
                macros.add("DEVICE", selected_camera.get("P", ""))
                macros.add("CAM", selected_camera.get("R", ""))
                
                # Plugin enable macros for dynamic UI
                macros.add("ROI_ENABLED", selected_camera.get("ROI_ENABLED", "0"))
                macros.add("PROC_ENABLED", selected_camera.get("PROC_ENABLED", "0"))
                macros.add("STATS_ENABLED", selected_camera.get("STATS_ENABLED", "0"))
                macros.add("OVERLAY_ENABLED", selected_camera.get("OVERLAY_ENABLED", "0"))
                macros.add("TIFF_ENABLED", selected_camera.get("TIFF_ENABLED", "1"))
                macros.add("STREAM_ENABLED", selected_camera.get("STREAM_ENABLED", "0"))
                
                logger.info("Set macros - DEVICE: " + selected_camera.get("P", "") + 
                           ", CAM: " + selected_camera.get("R", "") +
                           ", ROI: " + selected_camera.get("ROI_ENABLED", "0") +
                           ", PROC: " + selected_camera.get("PROC_ENABLED", "0") +
                           ", STATS: " + selected_camera.get("STATS_ENABLED", "0") +
                           ", OVERLAY: " + selected_camera.get("OVERLAY_ENABLED", "0") +
                           ", TIFF: " + selected_camera.get("TIFF_ENABLED", "1") +
                           ", STREAM: " + selected_camera.get("STREAM_ENABLED", "0"))
                
                # Reload the embedded display with new macros
                widget.setPropertyValue("file", "CameraV2_Main.bob")
            else:
                logger.warning("Camera not found in configuration: " + pv_value)

except Exception as e:
    logger.error("DeviceSelectV2 error: " + str(e))
