from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from java.io import FileReader, BufferedWriter, FileWriter
from org.csstudio.display.builder.model import WidgetFactory

from org.yaml.snakeyaml import Yaml
import os

pvset = {
    'mag': ["STATE_SP","CURRENT_SP"],
    'cool': ["STATE_SP","TEMP_SP"],
    'vac': []
}

pvrb = {
    'mag': ["CURRENT_RB","STATE_RB"],
    'cool': ["TEMP_RB","STATE_RB"],
    'vac': ["PRES_RB"]
}

pvsetrb = {
    'mag': ["STATE","CURRENT"],
    'cool': ["STATE","TEMP"],
}

def conf_to_iocs(confpath):
    """    Load the configuration from the YAML file and return the iocs section.
    """
    iocs=[]

    if not os.path.exists(confpath):
        ScriptUtil.showMessageDialog(widget, "## Cannot find file \"" + confpath + "\" please set CONFFILE macro to a correct file")
        return iocs
    yaml = Yaml()
    data = yaml.load(FileReader(confpath))
    epics_config = data.get("epicsConfiguration")
    if epics_config is None:
        ScriptUtil.showMessageDialog(widget, "Cannot find 'epicsConfiguration' in \"" + confpath + "\"")
        return iocs


    iocs = epics_config.get("iocs")
    if iocs is None:
        ScriptUtil.showMessageDialog(widget, "Cannot find iocs section, please provide a valid values.yaml file")
        return dev

    return iocs


def conf_to_dev(widget):
    devarray = []

    pvs = ScriptUtil.getPVs(widget)
    zoneSelector = widget.getEffectiveMacros().getValue("ZONE")
    typeSelector = widget.getEffectiveMacros().getValue("TYPE")
    if len(pvs)>0 and zoneSelector == None:
        zoneSelector = PVUtil.getString(pvs[0])
    elif zoneSelector is None:
        zoneSelector = "ALL"

    if len(pvs)>1 and typeSelector == None:
        typeSelector = PVUtil.getInt(pvs[1])
    elif typeSelector is None:
        typeSelector = "ALL"

    
    group=widget.getEffectiveMacros().getValue("GROUP")
    conffile = widget.getEffectiveMacros().getValue("CONFFILE")
    display_model = widget.getDisplayModel()
    display_path = os.path.dirname(display_model.getUserData(display_model.USER_DATA_INPUT_FILE))

    if conffile is None:
        ScriptUtil.showMessageDialog(widget, "## Please set CONFFILE macro to a correct YAML configuration file")
        return devarray
    
    if group == None:
        ScriptUtil.showMessageDialog(widget, "## Must Specify group widget (i.e unicool,univac,unimag) (GROUP Macro) \"" + confpath + "\" please set CONFFILE macro to a correct file")
        return devarray
    
    confpath = display_path + "/" + conffile    

    print("LOADING \""+group+"\" zoneSelector: \"" + zoneSelector + " typeSelector: \"" + str(typeSelector)+"\"")

    iocs = conf_to_iocs(confpath)
    for ioc in iocs:
        ioc_name = ioc.get("name", "")
        iocprefix = ioc.get("iocprefix", "")
        devtype = ioc.get("devtype", "ALL")
        devgroup = ioc.get("devgroup", "")
        devfunc  = ioc.get("devfunc", "")
        opi  = ioc.get("opi", "")
        zones = ioc.get("zones", "ALL")
        iocroot=ioc.get("iocroot", "")

        #print("Checking IOC:", ioc_name, "iocprefix:", iocprefix, "devtype:", devtype)    
        if iocprefix and devgroup == group:
            devices = ioc.get("devices", [])
            for dev in devices:
                name = dev['name']
                prefix=iocprefix
                devtype=ioc.get("devtype", "ALL")
                if 'devfunc' in ioc:
                    devfunc  = ioc.get("devfunc", "")
                else:
                    if ('HCV' in name) or ('VCR' in name) or ('CHH' in name) or ('CVV' in name):
                        devfunc="COR"
                    elif ('QUA' in name) or ('QUAD' in name):
                        devfunc="QUA"
                    elif ('DIP' in name) or ('DPL' in name) or ('DHS' in name) or ('DHR' in name) or ('DHP' in name):
                        devfunc="DIP"
                    elif ('SOL' in name) :
                        devfunc="SOL"
                    elif ('UFS' in name) :
                        devfunc="UFS"
                    elif('SIP' in name):
                        devfunc="ion"
                    

                if 'opi' in dev:
                    opi=dev['opi']
                if 'zones' in dev:
                    zones=dev['zones']
                if 'name' in dev:
                    iocroot=dev['name']
                if 'devfunc' in dev:
                    devfunc=dev['devfunc']
                if 'alias' in dev:
                    name=dev['alias']
                if 'prefix' in dev:
                    prefix=dev['prefix']
                # print(devgroup_widget+"-"+devtype+" filtering object "+str(dev))

                if zoneSelector and zoneSelector != "ALL" and zoneSelector not in zones:
                    continue
                if typeSelector and typeSelector != "ALL" and typeSelector != devfunc:
                    continue
                if len(zones)==1:
                    zone=zones[0]
                else:
                    zone=str(zones)

                if devfunc == "ion":
                    devfunc = "0"
                elif devfunc == "pig":
                    devfunc = "1"
                elif devfunc == "ccg":
                    devfunc = "2"

                devarray.append({'NAME':name,'R': iocroot, "P": prefix, "TYPE": devfunc, "ZONE": zone,"OPI":opi})
    return devarray

def dump_pv(widget,separator="\n"):
    
    """Dump the PVs to a file."""
    devarray = conf_to_dev(widget)
    group=widget.getEffectiveMacros().getValue("GROUP")

    if not devarray:
        ScriptUtil.showMessageDialog(widget, "No devices found for group: " + group)
        return
    pvlist = ""
    for dev in devarray:
        for pv in pvrb.get(group, []):
            pvlist = pvlist + dev['P']+":"+dev['R']+":"+pv+separator
    for dev in devarray:
        for pv in pvset.get(group, []):
            pvlist = pvlist + dev['P']+":"+dev['R']+":"+pv+separator


    return pvlist


def dump_pv_tofile(widget):
    """Dump the PVs to a file."""
    name=widget.getPropertyValue("name")
    group=widget.getEffectiveMacros().getValue("GROUP")
    name=ScriptUtil.showSaveAsDialog(widget, name)

    print("Dumping PVs for group: " + group+ " to file: " + name)
    devarray = conf_to_dev(widget)
    if not devarray:
        ScriptUtil.showMessageDialog(widget, "No devices found for group: " + group)
        return

    fcsvn= name + ".sar.csv"
    fcsvn_valueset_name= name + ".value_set.csv"
    fcsvn_valuerb_name= name + ".value_rb.csv"

        # Open a file for writing
    fcsv = open(fcsvn, 'w')
    fcsvn_set = open(fcsvn_valueset_name, 'w')
    fcsvn_rb = open(fcsvn_valuerb_name, 'w')
    fcsv.write("PV,READBACK,READ_ONLY\n")
    fcsvn_set.write("Name,Prefix,PV,Value\n")
    fcsvn_rb.write("Name,Prefix,PV,Value\n")
    for dev in devarray:
        for pv in pvset.get(group, []):
            prefix=dev['P']+":"+dev['R']
            pvname= prefix+":"+pv                       
            remote_pv = PVUtil.createPV(pvname, 100)
            val= str(remote_pv.read().getValue())
            fcsvn_set.write(dev['NAME'] + "," + prefix+ "," + pvname + "," + val+"\n")
        for pv in pvrb.get(group, []):
            pvname= dev['P']+":"+dev['R']+":"+pv                       
            remote_pv = PVUtil.createPV(pvname, 100)
            val= str(remote_pv.read().getValue())
            fcsvn_rb.write(dev['NAME'] + "," + prefix+ "," + pvname + "," + val+"\n")
        for pv in pvsetrb.get(group, []):
            fcsv.write(pvname + "_SP,"+pvname+"_RB,0\n")


    
    fcsv.close()
    fcsvn_set.close()
    fcsvn_rb.close()
    ScriptUtil.showMessageDialog(widget, "Generated \"" + fcsvn + "\" SAR file\ndumped SET values to \"" + fcsvn_valueset_name + "\"\ndumped RB values to \"" + fcsvn_valuerb_name + "\"\n")

def load_pv_fromfile(widget,name):
    wtemplate = ScriptUtil.findWidgetByName(widget, "element_template") ## name of the hidden template
    interlinea=5
    group = widget.getEffectiveMacros().getValue("GROUP")
    embedded_width  = wtemplate.getPropertyValue("width")
    embedded_height = wtemplate.getPropertyValue("height") +interlinea
    offy=0
    cnt=0
    bobname = "uni"+group+"-opi/"+group + "_channel_load.bob"
    if name.endswith(".csv"):
        # Load the CSV file
        data = csv_to_list(name)
        for row in data:
            pvname = row['PV']
            prefix = row['Prefix']

            value = row['Value']
            local_pv = PVUtil.createPV("loc://apply:"+pvname, 100)
            localok_pv = PVUtil.createPV("loc://apply:"+pvname+":ok", 100)
            local_pv.write(value)
            localok_pv.write(1)
            x=0
            y= offy+ cnt * (embedded_height)
            m={'PVNAME': pvname,"P":prefix,"R":row['Name']}
            instance = createInstance(embedded_width,embedded_height,pvname,bobname,x, y, m)
            widget.runtimeChildren().addChild(instance)
            cnt=cnt+1


   
def csv_to_list(csv_file):
    result = []

    with open(csv_file, 'r') as file:
        # Read lines from the file
        lines = file.readlines()
        # Extract the header
        header = [col.strip() for col in lines[0].split(",")]
        # Process each row
        for line in lines[1:]:
            values = [value.strip() for value in line.split(",")]
            row_dict = dict(zip(header, values))
            result.append(row_dict)
    return result


def createInstance(embedded_width,embedded_height,name,bobname,x, y, macros):
    embedded = WidgetFactory.getInstance().getWidgetDescriptor("embedded").createWidget()
    embedded.setPropertyValue("name", name)

    embedded.setPropertyValue("x", x)
    embedded.setPropertyValue("y", y)
    embedded.setPropertyValue("width", embedded_width)
    embedded.setPropertyValue("height", embedded_height)
    for macro, value in macros.items():
        embedded.getPropertyValue("macros").add(macro, value)

    embedded.setPropertyValue("file", bobname)
    return embedded