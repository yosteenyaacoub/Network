
import datetime as dt
from genie.testbed import load
from genie.utils.diff import Diff
from genie.conf import Genie
from pyats.topology import loader
import os,csv,sys,json,re,logging
import pandas as pd
import numpy as np
from cryptography.fernet import Fernet
from zoneinfo import ZoneInfo




#os.system('clear')
encrypted_password = b'***********=='

with open ('/directory/key','rb') as f: key = f.read()
Fernet = Fernet(key)
decrypted_password = Fernet.decrypt(encrypted_password).decode('utf-8')

def read_devices_from_csv(csv_file):
  devices = []
  with open(csv_file, 'r') as file:
      csv_reader = csv.DictReader(file)
      for row in csv_reader: devices.append(row)
  return devices



## Function to create a testbed from CSV without enable password

def create_testbed(devices):
    testbed_dict = {
        'devices': {}
    }
    for device in devices:
        testbed_dict['devices'][device['hostname']] = {
            'connections': {
                'cli': {
                    'ip': device['ip'],
                    'protocol': 'ssh'
                }
            },
            'credentials': {
                'default': {
                    'username': device['username'],
                    'password': decrypted_password
                }
            },
            'model': device['model'],
            'os': device['os'],
            'type': 'router'
        }
    return loader.load(testbed_dict)

def createTestBed(fileName):
 location = '/code/collectInfo/inventory/'+str(fileName)
 print (location)
 tempDict = read_devices_from_csv(location)
 tesbed = create_testbed(tempDict)
 return tesbed

#########################################################
## Create testbed from csv without hardcoding username, password
def create(devices):
    ## Creates testbed from csv file
    testbed_dict = {
        'devices': {}
    }
    for device in devices:
        testbed_dict['devices'][device['hostname']] = {
            'connections': {
                'cli': {
                    'ip': device['ip'],
                    'protocol': 'ssh'
                }
            },
            'credentials': {
                'default': {
                    'username': 'user1InsertHere',
                    'password': 'Password1InsertHere'
                }
            },
            'model': device['model'],
            'os': device['os'],
            'type': 'router'
        }
    return loader.load(testbed_dict)

def makeTestbed(fileName):
 location = '/directory/inventory/'+str(fileName)
 print (location)
 tempDict = read_devices_from_csv(location)
 tesbed = create(tempDict)
 return tesbed






def iosGetIPCIDR(device):
  fdf = pd.DataFrame()
  tdf = pd.DataFrame()
  try: 
     tempdf = pd.DataFrame()
     deviceName = device._name
     device.connect(init_exec_commands=[],init_config_commands=[],log_stdout=False)
     c = device.execute("show ip interface brief | ex unass")
     for line in c.splitlines():
        if 'nterf' in line: continue
        a = line.split()
        try:
          if a[0] != 'Loopback0': name = deviceName + '-' + a[0] ##remove loopback 0 to get device name only
          else: name = deviceName
        except: pass
        name = name.replace('/','-').replace('.','-')
        tempDict = {'name':name,'ip':a[1]}
        tempdf = pd.DataFrame([tempDict])
        fdf = pd.concat([fdf,tempdf])
     c1 = device.execute("show run | i ip.address") 
     for line in c1.splitlines():
       if 'no' in line: continue
       a = line.split()
       tempDict1 = {'ip':a[2],'CIDR':a[3]}
       tempdf1 = pd.DataFrame([tempDict1])
       tdf = pd.concat([tdf,tempdf1])
  except Exception as e:
     print (e)
     pass
  return fdf,tdf

