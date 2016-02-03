#!/usr/bin/env python

import subprocess, json, os, yaml
from utils import *
from optparse import OptionParser

cliparser = OptionParser()

cliparser.add_option("-f", "--file", dest="cfgfile",
                     help="This is the input config file used to define the test.",
                     metavar="FILE", default="pyconfig.yaml")
cliparser.add_option("-c", "--certpath", dest="cert",
                     default="/etc/origin/master/ca.crt",
                     help="The certificate path to login a user.")
cliparser.add_option("-o", "--passfile", dest="osepassfile",
                     default="/etc/origin/openshift-passwd",
                     help="Path to openshift-passwd file to add user's password.", )
cliparser.add_option("-n", "--namespace", dest="projectname",
                     help="Project/Namespace under which to run the test",
                     default="testproj00")
cliparser.add_option("-m", "--master", dest="osemaster",
                     default="https://ose3-master.example.com:8443",
                     help="The Adress of the OSE Master")
cliparser.add_option("-u", "--user", dest="oseuser", default="user00",
                     help="OSE user under which to run the test")
cliparser.add_option("-d", "--clean",
                     action="store_true", dest="cleanall", default=False,
                     help="Clean the openshift environment created by the test.")
cliparser.add_option("-v", "--debug",
                     action="store_true", dest="debug", default=False,
                     help="Prints more detailed info to help debug an issue.")

(options, args) = cliparser.parse_args()

# bashCommand = "id -u "+ oseuser " &>/dev/null | useradd "+ oseuser
# process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
# output = process.communicate()[0]
######

testconfig = {}
with open(options.cfgfile) as stream:
    testconfig = yaml.load(stream)

globalvars = {}
globalvars["cleanoption"] = options.cleanall
globalvars["debugoption"] = options.debug

# Call the main function
for config in testconfig["projects"]:
    if "tuning" in config:
        globalvars["tuningset"] = find_tuning(testconfig["tuningsets"], \
                                              config["tuning"])
    project_handler(config, globalvars)
