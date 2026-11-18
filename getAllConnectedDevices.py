import sys
sys.path.append('/code/collectInfo')
from functions import *
import requests
from genie.metaparser.util.exceptions import SchemaEmptyParserError
now = dt.datetime.now()
nowTime = str(now.strftime("%B-%d_%H-%M"))
import socket
os.system('clear')
def getsDns(ip):
    try:
      hostname,aliaslist, ipaddrlist = socket.gethostbyaddr(ip)
      return hostname
    except:
      return np.nan

def load_mac_db(path='/code/collectInfo/inventory/MacOUs.csv'):
    ## to refresh mac database => https://maclookup.app/downloads/csv-database
    df = pd.read_csv(path, usecols=[0, 1], header=0)
    df.columns = ['oui', 'company']
    # Normalize to uppercase, no separators
    df['oui'] = df['oui'].str.replace('[:\-]', '', regex=True).str.upper()
    return df.set_index('oui')['company'].to_dict()

MAC_DB = load_mac_db()  # Load ONCE at top of script
for k,v in MAC_DB.items():
  print (k,' ->', v)
  break 
def get_vendor(mac):
    oui = mac.replace(':', '').replace('-', '').replace('.','').upper()[:6]
    return MAC_DB.get(oui, 'Unknown')

#sys.exit()
arpDf = pd.DataFrame()
vrfDf = pd.DataFrame()
macDf = pd.DataFrame()

print ('\033[94m' + '>>>>> Running Command <<<<<<<'+ '\033[0m')

site = createTestBed('ProjectFile.csv')
i = 0
y = len(list(site))
for device in site:
  i += 1
  y = y - 1
  if "wanted switch" not in device.name: continue
  
  ## Get all VRFs
  try:
    print (device.name,'.'*y)
    device.connect(init_exec_commands=[],init_config_commands=[],log_stdout=False)
    vrfs = []
    try:
      ## get vrf for devices with vrfs
      vrfCmd = device.parse('show vrf')
      for vrf, v in vrfCmd['vrf'].items():
        #print ('___',vrf,'____',v,'\n')
        if vrf != "Mgmt-vrf": vrfs.append(vrf)
        #print (v)
        if v.get('interfaces'):
          for interface in  v.get('interfaces'):
            if 'Hundred' in interface: continue
            tempDict = {'switch':device.name,'interface':interface,'vrf':vrf}
            tempDf = pd.DataFrame([tempDict])
            vrfDf = pd.concat([vrfDf,tempDf])
      #print (vrfDf)
    except Exception as e:
      print (f'{device.name}, Issue with show vrf parsing_ ',e)
      pass
    print (vrfs)
    #break
    ######################################################
                            # A R P #
    ######################################################    
    ## Get ip arp for default vrf
    try:
      ## get arp for devices with no vrf
      command = device.parse(f'show ip arp')
      for interface,v in command['interfaces'].items():
        enteries = v['ipv4']['neighbors']
        for entry in v['ipv4']['neighbors'].values():
          mac = entry['link_layer_address']
          if "Hundred" in interface: continue
          dnsName = getsDns(entry['ip'])
          tempDict = {'switch':device.name,'interface':interface,'Name':dnsName,'ip':entry['ip'],'mac':mac}
          #print (tempDict)
          tempDf = pd.DataFrame([tempDict])
          arpDf = pd.concat([tempDf,arpDf])
    except Exception as e:
      print (e)
      print (f'{device.name}, 0 VRFs, Issue with show ip arp parsing',e)
      pass
      #break 

    ## Get ip arp for each vrf

    for vrf in vrfs:
      print ('starting',device.name,vrf)
      try:
        if vrf == 'default': command = device.parse(f'show ip arp')
        else: command = device.parse(f'show ip arp vrf {vrf}')
        for interface,v in command['interfaces'].items():
          if 'Hundred' in interface: continue
          enteries = v['ipv4']['neighbors']
          for entry in v['ipv4']['neighbors'].values():
            ip = entry['ip']
            dnsName = getsDns(ip)
            mac = entry['link_layer_address']
            tempDict = {'switch':device.name,'interface':interface,'Name':dnsName,'ip':entry['ip'],'mac':mac}
            #print (tempDict)
            tempDf = pd.DataFrame([tempDict])
            arpDf = pd.concat([tempDf,arpDf])
      except Exception as e:
        print ('Something wrong with vrf',device.name,vrf,e)
        pass
    #break
    ######################################################
                            # M A C#
    ######################################################
    
    #print ('Getting MAC address table')
    MaCmd = device.parse('show mac address-table')
    vlans =  MaCmd['mac_table']['vlans']
    for vlan,entery in vlans.items():
      if vlan == 'all': continue
      macs = entery['mac_addresses']
      if device.os == 'ios':
        for macD in macs.values(): 
          #print (macD)
          try:
            mac = macD['mac_address']
            if mac == 'ffff.ffff.ffff':continue
            interfaceD = macD['interfaces']
            interface = list(interfaceD.keys())[0]
            #print (interface)
            vendor = get_vendor(mac)
            tempDict = {'switch':device.name,'mac':mac,'vlan':vlan,'PhysInterface':interface,"vendor":vendor}
            #print (tempDict)
            tempdf = pd.DataFrame([tempDict])
            #break
            macDf = pd.concat([macDf,tempdf])    
          except Exception as e: 
            print ('mac issue',e)
            pass
      else:    ## IOS XE 
        for macD in macs.values(): 
          try:
            mac = macD['mac_address']
            if mac == 'ffff.ffff.ffff':continue
            interfaceD = macD['interfaces']
            interface = None
            for key in list(interfaceD.keys()): 
              if 'net' in key: interface = key
            vendor = get_vendor(mac)
            tempDict = {'switch':device.name,'mac':mac,'vlan':vlan,'PhysInterface':interface,"vendor":vendor}
            #print (tempDict)
            tempdf = pd.DataFrame([tempDict])
            #break
            macDf = pd.concat([macDf,tempdf])    
          except Exception as e: 
            print ('mac issue',e)
            pass
  ##############################    
  except Exception as e:
    print (f"\033[31m {device.name} issue with Mac address tabel, {e}  \033[0m")
    pass
  finally: 
    if device.connected: device.disconnect()
  #if i == 3: break
    
#sys.exit()
#print (arpDf.head(2))
#print (macDf.head(2))
#sys.exit()
if vrfDf.shape[0] != 0:
  print ('vrf shape > 0')
  df = pd.merge(arpDf,vrfDf,on=['switch','interface'],how='outer')
  df = pd.merge(df,macDf,on=['switch','mac'],how='outer')
else:
  print ('vrf shape = 0')
  df = pd.merge(arpDf, macDf, on=['switch','mac'], how='outer')

#print (df)
#sys.exit()
df = df.sort_values(by='switch')
print (df.head(30))
print (df.tail(30))
df.to_csv("reports/output.csv")
print (" - - -  D O N E - - - -")
"""
switch ip mac vendor l3interface physinterface
"""
