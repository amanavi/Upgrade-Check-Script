#!/usr/bin/python3
import argparse
import tarfile
import os
import json
import sys
#import re

def check_files():
    #Add logic to check if logs are collected correctly
    return True

def intro():
    print("This Script will check below parameters:\n\
 1. Current Controller and SE version+patch\n\
 2. Cloud type\n\
 3. Total number of VSes\n\
 4. Controller - CPU / Mem / Total disk space / Used disk space\n\
 5. Using BGP\n\
 6. Using Pool Groups with connection multiplex disabled\n\
 7. Is http to https redirect disabled in Controller system setting\n\
 8. Is there an IP access list for Controller Management IP\n\
 9. Is the field 'waf_learning_memory' present in any SE group config\n\
 10.Are there custom Pool HMs with custom headers configured\n\
 11.Using Parent/Child VS\n\
 12.Is this a GSLB leader or follower site\n\n\
Verify manually below parameters:\n\
 1. SE Disk Space\n\
 2. SE Patch Versions\n\
")


def tar(path):
    '''
    dlist = []
    for root,dirc,files in os.walk(path):
        for filename in files:
           dlist.append(os.path.join(os.path.realpath(root),filename))
    for i in dlist:
        if ".tar.gz" in i:
            print("Extracting: " +i.split("/")[-1])
            tf = tarfile.open(i)
            tf.extractall(os.path.dirname(i))
            tf.close()
    print("Extraction of debug logs complete.")
    '''
    tlist = []
    for root1,dirc1,files1 in os.walk(path):
        for filename1 in files1:
           tlist.append(os.path.join(os.path.realpath(root1),filename1))
    for j in tlist:
        if "node.tar.gz" in j:
            if os.path.isdir(os.path.dirname(j)+'/var'):
                print("Already Extracted: " +j.split("/")[-2]+"/"+j.split("/")[-1])
            else:
                print("Extracting: " +j.split("/")[-2]+"/"+j.split("/")[-1])
                tf = tarfile.open(j)
                try:
                    tf.extractall(os.path.dirname(j))
                except PermissionError:
                    print("PermissionError: Run the command with Sudo; Exiting now")
                    sys.exit()
                    tf.close()
    print("Extraction of Node logs complete.")
    return

def dir_list(path):
    global dirlist
    dirlist = []
    for root,dirc,files in os.walk(path):
        for filename in files:
           dirlist.append(os.path.join(os.path.realpath(root),filename))
    return dirlist

def avi_config():
    global config
    for i in dirlist:
        if i.split('/')[-1] == "avi_config":
            f = open(i,'r')
            config = json.load(f)
            f.close()
    try:
        if config:
            pass
        else:
            print("Fatal Error: Avi Config not present/found; Exiting now")
            sys.exit()
    except NameError:
        print("Fatal Error: Avi Config not present/found; Exiting now")
        sys.exit()
    return

#Current Controller and SE version+patch?
def versions():
    header("Controller and SE Version with Patch details")
    print("Controller Version: ",config["META"]["version"]["Version"])
    print("Controller Build: ",config["META"]["version"]["build"])
    print("Controller Patch: ", end="")
    try:
        print(config["META"]["version"]["patch"])
    except KeyError:
        print("No Patch")
    print("SE Patch Installed: ", end="")
    try:
        print(config["META"]["version"]["se_patch"])
    except KeyError:
        print("No Patch")

#Cloud type(s): AWS, LSC, VMware, etc
def cloud():
    header("Cloud Name and Type")
    for i in range(len(config["Cloud"])):
        print(str(i+1) + '. Name: '+ config["Cloud"][i]["name"] + " Type: " + str(config["Cloud"][i]["vtype"]))

#Total number of VSes
def vs():
    header("No of Virtual Services")
    print("No of VS: ", len(config["VirtualService"]))

#Controller - CPU / Mem / Total disk space / Used disk space
def res():
    '''debuglogs.20190727-024623/tech_node1.controller.local-172.28.3.196/var/log/system_details.log'''
    header("Controller Resources")
    for i in dirlist:
        if i.split('/')[-1] == "system_details.log":
            f = open(i,'r')
            details = f.readlines()
            f.close()
            print("Node: " + i.split('/')[-4])
            cpu = []
            for j, line in enumerate(details):
                if "MemTotal" in line:
                    print(line.strip())
                if "MemFree" in line:
                    print(line.strip())
                if "MemAvailable" in line:
                    print(line.strip(),'\n')

                if "avinetworks/controller:" in line:
                    ln = line.strip("\t")
                    print("Docker Info: ID- ", ln.split()[0])

                if "cpu cores" in line:
                    cpu.append(int((line.strip()).split(" ")[-1]))
            print("No of CPUs: ", str(len(cpu)), "\tNo of Cores: ", str(sum(cpu)), '\nk')

#Using BGP or not
def bgp():
    header("BGP Info")
    a = 0
    for i in range(len(config["VrfContext"])):
        try:
            print("BGP enabled in VRF: ", config["VrfContext"][i]["name"], "\tNo of Peers: ", len(config["VrfContext"][i]["bgp_profile"]["peers"]))
            a += 1
        except KeyError:
            pass
    if a == 0:
        print("No BGP Peers configured")

#Using Pool Groups with cx multiplex disabled?
def pool_multx():
    header("Connection Multiplex")
    print("VSs with Pool Groups having Connection Multiplex Disabled: ")
    app_prof = []
    for i in range(len(config["ApplicationProfile"])):
       try:
          if config["ApplicationProfile"][i]["http_profile"]['connection_multiplexing_enabled'] == False:
             app_prof.append(config["ApplicationProfile"][i]["name"])
       except:
          pass
    for j in range(len(config["VirtualService"])):
       for k in app_prof:
          if (config["VirtualService"][j]['application_profile_ref']).split("&name=")[-1] == k:
             try:
                print("VS: ", config["VirtualService"][j]["name"], "\tPG: ", (config["VirtualService"][j]['pool_group_ref'].split("&name="))[-1].split("&cloud=")[-2])
             except:
                pass

#Is http to https redirect disabled in Controller system setting?
def redirect():
    header("Redirect")
    for i in range(len(config["SystemConfiguration"])):
        print("Redirect HTTP to HTTPS: ", config["SystemConfiguration"][i]["portal_configuration"]["redirect_to_https"])

#Are there custom Pool HMs with custom headers configured?
def custom_hm():
    header("Health Monitor")
    print("HMs with Custom Headers:")
    for i in range(len(config["HealthMonitor"])):
       try:
          if config["HealthMonitor"][i]['http_monitor']['http_request'] or config["HealthMonitor"][i]['https_monitor']['http_request']:
             print(config["HealthMonitor"][i]["name"])
       except:
          pass

#Using Parent/Child VS?
def parent():
    header("Virtual Hosting")
    print("Check if using Parent/Child VS:")
    p,c = 0,0
    for i in range(len(config["VirtualService"])):
        if config["VirtualService"][i]["type"] == "VS_TYPE_VH_CHILD":
            c += 1
        elif config["VirtualService"][i]["type"] == "VS_TYPE_VH_PARENT":
            p += 1
        else:
            pass
    print("Parent VS Count: ", p, "\nChild VS Count: ", c)

#Is this a GSLB leader or follower site?
def gslb():
    header("GSLB")
    try:
        if config['Gslb'] == []:
            print("GSLB not configured.")
        else:
            if config['Gslb'][0]["uuid"] == config['Gslb'][0]["leader_cluster_uuid"]:
                print("This Site is GSLB Leader: ", config['Gslb'][0]["name"])
                print("Total Sites are: ", len(config['Gslb'][0]["sites"]))
            else:
                print("Site is Follower: ", config['Gslb'][0]["name"])
                for i in range(len(config['Gslb'][0]["sites"])):
                    if config['Gslb'][0]['sites'][i]['uuid'] == config['Gslb'][0]['leader_cluster_uuid']:
                        print("GSLB Leader Site is: ", config['Gslb'][0]['sites'][i]['name'])
    except KeyError:
        print("GSLB Config not found.")

#Is there an IP access list for Controller Management IP?
def access_list():
    header("Controller Management Access")
    try:
        if 'ssh_access' in config['SystemConfiguration'][0]["mgmt_ip_access_control"]:
            print("Controller Management IP: SSH ACCESS LIST is Configured")
        if "api_access" in config['SystemConfiguration'][0]["mgmt_ip_access_control"]:
            print("Controller Management IP API ACCESS LIST is Configured")
    except KeyError:
        print("Controller Management IP: Access List is not configured")

#Is the field "waf_learning_memory" present in any SE group config?
def waf_mem():
    header("WAF")
    print("Checking if 'waf_learning_memory' present in SE group config: ")
    for i in range(len(config["ServiceEngineGroup"])):
      try:
        if 'waf_learning_memory' in config["ServiceEngineGroup"][i]:
          print(config["ServiceEngineGroup"][i]["name"])
      except:
        pass

def header(text):
    print("\n======================================================")
    print("=", text.center(50), "=")
    print("======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Script to print checklist for upgrading Avi Controllers")
    parser.add_argument("-p", "--path", required=True, help="Path to Avi Debug logs")
    args = parser.parse_args()
    path = args.path

    intro()

    check_files()

    tar(path)

    dir_list(path)
    avi_config()

    try:
        versions()
        cloud()
        vs()
        res()
        bgp()
        redirect()
        custom_hm()
        pool_multx()
        waf_mem()
        parent()
        gslb()
    except:
        print("An Exception Occured!")

if __name__ == "__main__":
    main()
