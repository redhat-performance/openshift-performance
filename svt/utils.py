#!/usr/bin/python

import json, subprocess, time, copy, sys
from datetime import datetime


def calc_time(timestr):
    tlist = timestr.split()
    if tlist[1] == "s":
        return int(tlist[0])
    elif tlist[1] == "min":
        return int(tlist[0]) * 60
    elif tlist[1] == "ms":
        return int(tlist[0]) / 1000
    elif tlist[1] == "hr":
        return int(tlist[0]) * 3600
    else:
        print "Invalid delay in rate_limit\nExitting ........"
        sys.exit()


def create_template(templatefile, num, parameters, globalvars):
    if globalvars["debugoption"]:
        print "create_template function called"

    namespace = globalvars["namespace"]
    data = {}
    timings = {}
    i = 0
    while i < int(num):
        templatejson = copy.deepcopy(data)
        cmdstring = "oc process -f %s" % templatefile
        
        if parameters:
            for parameter in parameters:
                for key, value in parameter.iteritems():
                    cmdstring += " -v %s=%s" % (key, value)
        cmdstring += " -v IDENTIFIER=%i" % i

        processedstr = subprocess.check_output(cmdstring, shell=True)
        templatejson = json.loads(processedstr)
        with open('/tmp/processed_template.json', 'w') as outfile:
            json.dump(templatejson, outfile)
        check = subprocess.call( \
            "oc create -f /tmp/processed_template.json " + \
            "--namespace %s" % namespace, shell=True)

        if "tuningset" in globalvars:
            if "templates" in globalvars["tuningset"]:
                templatestuningset = globalvars["tuningset"]["templates"]
                if "stepping" in templatestuningset:
                    stepsize = templatestuningset["stepping"]["stepsize"]
                    pause = templatestuningset["stepping"]["pause"]
                    globalvars["totaltemplates"] = globalvars["totaltemplates"] + 1
                    templates_created = int(globalvars["totaltemplates"])
                if templates_created % stepsize == 0:
                    time.sleep(calc_time(pause))
                if "rate_limit" in templatestuningset:
                    delay = templatestuningset["rate_limit"]["delay"]
                    time.sleep(calc_time(delay))

        i = i + 1


def create_service(servconfig, num, globalvars):
    if globalvars["debugoption"]:
        print "create_service function called"

    data = {}
    timings = {}
    data = servconfig
    i = 0
    while i < int(num):
        dataserv = copy.deepcopy(data)
        servicename = dataserv["metadata"]["name"] + str(i)
        dataserv["metadata"]["name"] = servicename
        with open('/tmp/service.json', 'w') as outfile:
            json.dump(dataserv, outfile)
        check = subprocess.call("oc create -f /tmp/service.json", \
                                shell=True)
        i = i + 1
        del (dataserv)


def create_pods(podcfg, num, globalvars):
    if globalvars["debugoption"]:
        print "create_pods function called"

    namespace = podcfg["metadata"]["namespace"]
    data = {}
    timings = {}
    data = podcfg
    i = 0
    pend_pods = globalvars["pend_pods"]
    while i < int(num):
        datapod = copy.deepcopy(data)
        podname = datapod["metadata"]["name"] + str(i)
        datapod["metadata"]["name"] = podname
        with open('/tmp/pod.json', 'w') as outfile:
            json.dump(datapod, outfile)
        check = subprocess.call("oc create -f /tmp/pod.json", \
                                shell=True)
        pend_pods.append(podname)

        if "tuningset" in globalvars:
            if "stepping" in globalvars["tuningset"]:
                stepsize = globalvars["tuningset"]["stepping"]["stepsize"]
                pause = globalvars["tuningset"]["stepping"]["pause"]
                globalvars["totalpods"] = globalvars["totalpods"] + 1
                total_pods_created = int(globalvars["totalpods"])
                if total_pods_created % stepsize == 0:
                    pod_data(globalvars)
                    time.sleep(calc_time(pause))
            if "rate_limit" in globalvars["tuningset"]:
                delay = globalvars["tuningset"]["rate_limit"]["delay"]
                time.sleep(calc_time(delay))

        i = i + 1
        del (datapod)


def pod_data(globalvars):
    if globalvars["debugoption"]:
        print "pod_data function called"

    pend_pods = globalvars["pend_pods"]
    namespace = globalvars["namespace"]

    while len(pend_pods) > 0:
        getpods = subprocess.check_output("oc get pods -n " + namespace, \
                                          shell=True)
        all_status = getpods.split("\n")

        size = len(all_status)
        all_status = all_status[1:size - 1]
        for status in all_status:
            fields = status.split()
            if fields[2] == "Running" and fields[0] in pend_pods:
                pend_pods.remove(fields[0])
        time.sleep(10)


def create_rc(rc_config, num, globalvars):
    if globalvars["debugoption"]:
        print "create_rc function called"

    i = 0
    data = rc_config
    basename = rc_config["metadata"]["name"]

    while i < num:
        curdata = copy.deepcopy(data)
        newname = basename + str(i)
        curdata["metadata"]["name"] = newname
        curdata["spec"]["selector"]["name"] = newname
        curdata["spec"]["template"]["metadata"]["labels"]["name"] = newname

        with open('/tmp/rc.json', 'w') as outfile:
            json.dump(curdata, outfile)
        subprocess.call("oc create -f /tmp/rc.json", shell=True)

        i = i + 1
        del (curdata)


def create_user(usercfg, globalvars):
    if globalvars["debugoption"]:
        print "create_user function called"

    namespace = globalvars["namespace"]
    basename = usercfg["basename"]
    num = int(usercfg["num"])
    role = usercfg["role"]
    password = usercfg["password"]
    passfile = usercfg["userpassfile"]

    i = 0
    while i < num:
        name = basename + str(i)
        # TO BE DISCUSSED
        # cmdstring = "id -u " + name + " &>/dev/null | useradd " + name
        # subprocess.call(cmdstring, shell=True)
        subprocess.call("htpasswd -c -b " + passfile + " " + name + " " + \
                        password, shell=True)
        subprocess.call("oadm policy add-role-to-user " + role + " " + name + \
                        " -n " + namespace, shell=True)
        print "Created User: " + name + " :: " + "Project: " + namespace + \
              " :: " + "role: " + role
        i = i + 1


def project_handler(testconfig, globalvars):
    if globalvars["debugoption"]:
        print "project_handler function called"

    total_projs = testconfig["num"]
    basename = testconfig["basename"]
    tuningset = globalvars["tuningset"]

    projlist = []
    i = 0
    while i < int(total_projs):
        projname = basename + str(i)
        subprocess.call("oc new-project " + projname, shell=True)
        projlist.append(projname)
        i = i + 1

    for proj in projlist:
        globalvars["namespace"] = proj
        if "templates" in testconfig:
            template_handler(testconfig["templates"], globalvars)
        if "services" in testconfig:
            service_handler(testconfig["services"], globalvars)
        if "users" in testconfig:
            user_handler(testconfig["users"], globalvars)
        if "pods" in testconfig:
            if "pods" in tuningset:
                globalvars["tuningset"] = tuningset["pods"]
            pod_handler(testconfig["pods"], globalvars)
        if "rcs" in testconfig:
            rc_handler(testconfig["rcs"], globalvars)


def template_handler(templates, globalvars):
    if globalvars["debugoption"]:
        print "template_handler function called"

    print "templates: ", templates
    for template in templates:
        num = int(template["num"])
        templatefile = template["file"]
        
        if "parameters" in template:
            parameters = template["parameters"]
        else:
            parameters = None
        if "tuningset" in globalvars:
            if "templates" in globalvars["tuningset"]:
                if "stepping" in globalvars["tuningset"]["templates"]:
                    globalvars["totaltemplates"] = 0

        create_template(templatefile, num, parameters, globalvars)

    if "totaltemplates" in globalvars:
        del (globalvars["totaltemplates"])


def service_handler(inputservs, globalvars):
    if globalvars["debugoption"]:
        print "service_handler function called"

    namespace = globalvars["namespace"]

    for service in inputservs:
        num = int(service["num"])
        servfile = service["file"]
        basename = service["basename"]

        if servfile == "default":
            servfile = "content/service-default.json"

        service_config = {}
        with open(servfile) as stream:
            service_config = json.load(stream)
        service_config["metadata"]["namespace"] = namespace
        service_config["metadata"]["name"] = basename

        create_service(service_config, num, globalvars)


def pod_handler(inputpods, globalvars):
    if globalvars["debugoption"]:
        print "pod_handler function called"

    namespace = globalvars["namespace"]
    total_pods = int(inputpods[0]["total"])
    inputpods = inputpods[1:]

    globalvars["pend_pods"] = []
    if "tuningset" in globalvars:
        if "stepping" in globalvars["tuningset"]:
            globalvars["totalpods"] = 0

    for podcfg in inputpods:
        num = int(podcfg["num"]) * total_pods / 100
        podfile = podcfg["file"]
        basename = podcfg["basename"]

        if podfile == "default":
            podfile = "content/pod-default.json"

        pod_config = {}
        with open(podfile) as stream:
            pod_config = json.load(stream)
        pod_config["metadata"]["namespace"] = namespace
        pod_config["metadata"]["name"] = basename

        create_pods(pod_config, num, globalvars)

    if len(globalvars["pend_pods"]) > 0:
        pod_data(globalvars)

    del (globalvars["tuningset"])
    del (globalvars["pend_pods"])
    del (globalvars["totalpods"])


def rc_handler(inputrcs, globalvars):
    if globalvars["debugoption"]:
        print "rc_handler function called"

    namespace = globalvars["namespace"]

    for rc_cfg in inputrcs:
        num = int(rc_cfg["num"])
        replicas = int(rc_cfg["replicas"])
        rcfile = rc_cfg["file"]
        basename = rc_cfg["basename"]
        image = rc_cfg["image"]

        if rcfile == "default":
            rcfile = "content/rc-default.json"

        rc_config = {}
        with open(rcfile) as stream:
            rc_config = json.load(stream)
        rc_config["metadata"]["namespace"] = namespace
        rc_config["metadata"]["name"] = basename
        rc_config["spec"]["replicas"] = replicas
        rc_config["spec"]["template"]["spec"]["containers"][0]["image"] = image

        create_rc(rc_config, num, globalvars)


def user_handler(inputusers, globalvars):
    if globalvars["debugoption"]:
        print "user_handler function called"

    for user in inputusers:
        create_user(user, globalvars)


def clean_all(globalvars):
    if globalvars["debugoption"]:
        print "clean_all function called"

    environment = globalvars["environ"]

    for project in environment:
        if "templates" in project:
            clean_templates(project["templates"])
            if "services" in project:
                clean_services(project["services"])
            if "pods" in project:
                clean_pods(project["pods"])
            if "rcs" in project:
                clean_rcs(project["rcs"])
            if "users" in project:
                clean_users(project["users"])

            subprocess.call("oc delete project " + project["name"], shell=True)


def clean_templates(templates):
    print "Cleaining all templates!!"
    for template in templates:
        data = {}
        num = len(templates)
        i = 0
        while i < int(num):
            templatejson = copy.deepcopy(data)
            cmdstring = "oc process -f %s" % templatefile
            for parameter in parameters:
                for key, value in parameter.iteritems():
                    cmdstring += " -v %s=%s" % (key, value)
                cmdstring += " -v IDENTIFIER=%i" % i

            processedstr = subprocess.check_output(cmdstring, shell=True)
            templatejson = json.loads(processedstr)
            with open('/tmp/processed_template.json', 'w') as outfile:
                json.dump(templatejson, outfile)
            subprocess.call("oc delete -f /tmp/processed_template.json", shell=True)


def clean_services(services):
    for service in services:
        subprocess.call("oc delete service " + service, shell=True)


def clean_pods(rcs):
    for pod in pods:
        subprocess.call("oc delete pod " + pod, shell=True)


def clean_rcs(rcs):
    for rc in rcs:
        subprocess.call("oc delete rc " + rc, shell=True)


def clean_users(users):
    for user in users:
        subprocess.call("oc delete user " + user, shell=True)


def find_tuning(tuningsets, name):
    for tuningset in tuningsets:
        if tuningset["name"] == name:
            return tuningset
        else:
            continue

    print "Failed to find tuningset: " + name + "\nExiting....."
    sys.exit()
