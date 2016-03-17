#!/usr/bin/env python

import json, subprocess, time, copy, sys, os, yaml, tempfile, shutil
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


def oc_command(args, globalvars):
    tmpfile=tempfile.NamedTemporaryFile()
    # see https://github.com/openshift/origin/issues/7063 for details why this is done. 
    shutil.copyfile(globalvars["kubeconfig"], tmpfile.name)
    ret = subprocess.check_output("KUBECONFIG="+tmpfile.name+" "+args, shell=True)
    if globalvars["debugoption"]:
        print args
    if args.find("oc process") == -1:
        print ret 
    tmpfile.close()
    return ret

def login(user,passwd,master):
    return subprocess.check_output("oc login -u " + user + " -p " + passwd + " " + master,shell=True)


def create_template(templatefile, num, parameters, globalvars):
    if globalvars["debugoption"]:
        print "create_template function called"

    namespace = globalvars["namespace"]
    data = {}
    timings = {}
    i = 0
    while i < int(num):
        tmpfile=tempfile.NamedTemporaryFile()
        templatejson = copy.deepcopy(data)
        cmdstring = "oc process -f %s" % templatefile
        
        if parameters:
            for parameter in parameters:
                for key, value in parameter.iteritems():
                    cmdstring += " -v %s=%s" % (key, value)
        cmdstring += " -v IDENTIFIER=%i" % i

        processedstr = oc_command(cmdstring, globalvars)
        templatejson = json.loads(processedstr)
        json.dump(templatejson, tmpfile)
        tmpfile.flush()
        if globalvars["kubeopt"]:
            check = oc_command("kubectl create -f "+tmpfile.name + \
                " --namespace %s" % namespace, globalvars)
        else:
            check = oc_command("oc create -f "+ tmpfile.name + \
                " --namespace %s" % namespace, globalvars)
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
        tmpfile.close()


def create_service(servconfig, num, globalvars):
    if globalvars["debugoption"]:
        print "create_service function called"

    data = {}
    timings = {}
    data = servconfig
    i = 0
    while i < int(num):
        tmpfile=tempfile.NamedTemporaryFile()
        dataserv = copy.deepcopy(data)
        servicename = dataserv["metadata"]["name"] + str(i)
        dataserv["metadata"]["name"] = servicename
        json.dump(dataserv, tmpfile)
        tmpfile.flush()

        if globalvars["kubeopt"]:
            check = oc_command("kubectl create -f " + tmpfile.name, \
                globalvars)
        else:
            check = oc_command("oc create -f " + tmpfile.name, \
                globalvars)
        i = i + 1
        del (dataserv)
        tmpfile.close()


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
        tmpfile=tempfile.NamedTemporaryFile()
        datapod = copy.deepcopy(data)
        podname = datapod["metadata"]["name"] + str(i)
        datapod["metadata"]["name"] = podname
        globalvars["curprojenv"]["pods"].append(podname)
        json.dump(datapod, tmpfile)
        tmpfile.flush()
        if globalvars["kubeopt"]:
            check = oc_command("kubectl create -f --validate=false " \
                + tmpfile.name, globalvars)
        else:
            check = oc_command("oc create -f " + tmpfile.name, \
                globalvars)
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
        tmpfile.close()


def pod_data(globalvars):
    if globalvars["debugoption"]:
        print "pod_data function called"

    pend_pods = globalvars["pend_pods"]
    namespace = globalvars["namespace"]

    while len(pend_pods) > 0:
        if globalvars["kubeopt"]:
            getpods = oc_command("kubectl get pods -n " + namespace, globalvars)
        else:
            getpods = oc_command("oc get pods -n " + namespace, globalvars)
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
        tmpfile=tempfile.NamedTemporaryFile()
        curdata = copy.deepcopy(data)
        newname = basename + str(i)
        globalvars["curprojenv"]["rcs"].append(newname)
        curdata["metadata"]["name"] = newname
        curdata["spec"]["selector"]["name"] = newname
        curdata["spec"]["template"]["metadata"]["labels"]["name"] = newname
        json.dump(curdata, tmpfile)
        tmpfile.flush()
        if globalvars["kubeopt"]:
            oc_command("kubectl create -f " + tmpfile.name, globalvars)
        else:
            oc_command("oc create -f " + tmpfile.name, globalvars)
        i = i + 1
        del (curdata)
        tmpfile.close()


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
        globalvars["curprojenv"]["users"].append(name)
        # TO BE DISCUSSED
        # cmdstring = "id -u " + name + " &>/dev/null | useradd " + name
        # subprocess.check_call(cmdstring, shell=True)
        if not os.path.isfile(passfile):
            subprocess.check_call("touch " + passfile, shell = True)
        subprocess.check_call("htpasswd -b " + passfile + " " + name + " " + \
                        password, shell=True)
        oc_command("oadm policy add-role-to-user " + role + " " + name + \
                        " -n " + namespace, globalvars)
        print "Created User: " + name + " :: " + "Project: " + namespace + \
              " :: " + "role: " + role
        i = i + 1

def single_project(testconfig, projname, globalvars): 
    if globalvars["kubeopt"]:
        with open("content/namespace-default.yaml") as infile:
            nsconfig = yaml.load(infile)
        nsconfig["metadata"]["name"] = projname
        with open('/tmp/namespace.yaml', 'w+') as f:
            yaml.dump(nsconfig, f, default_flow_style=False)
        oc_command("kubectl create -f /tmp/namespace.yaml",globalvars)
        oc_command("kuebctl label --overwrite namespace " + projname +" purpose=test", globalvars)
    else:
        oc_command("oc new-project " + projname,globalvars)      
        oc_command("oc label --overwrite namespace " + projname +" purpose=test", globalvars)
    
    time.sleep(1)
    projenv={}

    if "tuningset" in globalvars:
        tuningset = globalvars["tuningset"]
    if "tuning" in testconfig:
        projenv["tuning"] = testconfig["tuning"]
    globalvars["curprojenv"] = projenv  
    globalvars["namespace"] = projname
    if "quota" in testconfig:
        quota_handler(testconfig["quota"],globalvars)
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


def project_handler(testconfig, globalvars):
    if globalvars["debugoption"]:
        print "project_handler function called"

    total_projs = testconfig["num"]
    basename = testconfig["basename"]
    globalvars["env"] = []
    maxforks = globalvars["processes"]

    projlist = []
    i = 0
    while i < int(total_projs):
        j=0
        children = []
        while j < int(maxforks) and i < int(total_projs):
            j=j+1
            pid = os.fork()
            if pid:
                children.append(pid)
                i = i + 1
            else:
                projname = basename + str(i)
                print "forking %s"%projname
                single_project(testconfig, projname, globalvars)
                os._exit(0)
        for k, child in enumerate(children):
            os.waitpid(child, 0)


def quota_handler(inputquota, globalvars):
    if globalvars["debugoption"]:
        print "Function :: quota_handler"

    quota = globalvars["quota"]
    quotafile = quota["file"]
    if quotafile == "default":
        quotafile = "content/quota-default.json"

    with open(quotafile,'r') as infile:
        qconfig = json.load(infile)
    qconfig["metadata"]["namespace"] = globalvars["namespace"]
    qconfig["metadata"]["name"] = quota["name"]
    tmpfile=tempfile.NamedTemporaryFile()
    json.dump(qconfig,tmpfile)
    tmpfile.flush()
    if globalvars["kubeopt"]:
        oc_command("kubectl create -f " + tmpfile.name, globalvars)
    else:
        oc_command("oc create -f " + tmpfile.name, globalvars)
    tmpfile.close()


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
    globalvars["curprojenv"]["services"] = []

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
    globalvars["curprojenv"]["pods"] = []
    if "tuningset" in globalvars:
        globalvars["podtuningset"] = globalvars["tuningset"]
    
    globalvars["pend_pods"] = []
    if "podtuningset" in globalvars:
        if "stepping" in globalvars["podtuningset"]:
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

    if "podtuningset" in globalvars:
        del(globalvars["podtuningset"])
        del(globalvars["totalpods"])
    del(globalvars["pend_pods"])
    

def rc_handler(inputrcs, globalvars):
    if globalvars["debugoption"]:
        print "rc_handler function called"

    namespace = globalvars["namespace"]
    globalvars["curprojenv"]["rcs"] = []
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

    globalvars["curprojenv"]["users"] = []

    for user in inputusers:
        create_user(user, globalvars)


def clean_all(globalvars):
    if globalvars["debugoption"]:
        print "clean_all function called"

    with open("current_environment.json","r") as infile:
        environment = json.load(infile)

    for project in environment:
        globalvars["namespace"] = project["name"]
        if "tuning" in project:
            globalvars["tuning"] = True
            globalvars["tuningset"] = find_tuning(globalvars["tuningsets"],\
                project["tuning"])
#        if "templates" in project:
#            clean_templates(project["templates"],globalvars)
        if "services" in project:
            clean_services(project["services"], globalvars)
        if "pods" in project:
            clean_pods(project["pods"], globalvars)
        if "rcs" in project:
            clean_rcs(project["rcs"], globalvars)
        if "users" in project:
            clean_users(project["users"], globalvars)
        if "quota" in project:
            clean_quotas(project["quota"], globalvars)

        if globalvars["kubeopt"]:
            oc_command("kubectl delete project " + project["name"], globalvars)
        else:
            oc_command("oc delete project " + project["name"], globalvars)


#def clean_templates(templates,globalvars):
#    print "Cleaning all templates!!"
#    for template in templates:
#        data = {}
#        num = len(templates)
#        i = 0
#        while i < int(num):
#            tmpfile=tempfile.NamedTemporaryFile()
#            templatejson = copy.deepcopy(data)
#            cmdstring = "oc process -f %s" % templatefile
#            for parameter in parameters:
#                for key, value in parameter.iteritems():
#                    cmdstring += " -v %s=%s" % (key, value)
#                cmdstring += " -v IDENTIFIER=%i" % i
#
#            processedstr = oc_command(cmdstring, globalvars)
#            templatejson = json.loads(processedstr)
#            json.dump(templatejson, tmpfile)
#            tmpfile.flush()
#            if globalvars["kubeopt"]:
#                oc_command("kubectl delete -f "+ tmpfile.name, globalvars)
#            else:
#                oc_command("oc delete -f "+ tmpfile.name, globalvars)
#            tmpfile.close()


def clean_services(services, globalvars):
    for service in services:
        if globalvars["kubeopt"]:
            oc_command("kubectl delete service " + service + " -n " + \
                globalvars["namespace"], globalvars)
        else:
            oc_command("oc delete service " + service + " -n " + \
                globalvars["namespace"], globalvars)


def clean_pods(pods, globalvars):
    if "tuningset" in globalvars:
        if "pods" in globalvars["tuningset"]:
            globalvars["podtuningset"] = globalvars["tuningset"]["pods"]
    if "podtuningset" in globalvars:
        if "stepping" in globalvars["podtuningset"]:
            step = 0
            pend_pods = []
            pause = globalvars["podtuningset"]["stepping"]["pause"]
            stepsize = globalvars["podtuningset"]["stepping"]["stepsize"]
    for pod in pods:
        if "podtuningset" in globalvars:
            if "stepping" in globalvars["podtuningset"]:
                pend_pods.append(pod)
                if step >= stepsize:
                    delete_pod(pend_pods,globalvars)
                    step = 0
                    time.sleep(calc_time(pause))
                step = step + 1
            if "rate_limit" in globalvars["podtuningset"]:
                delay = globalvars["podtuningset"]["rate_limit"]["delay"]
                time.sleep(calc_time(delay))

        if globalvars["kubeopt"]:
            oc_command("kubectl delete pod " + pod + " -n " + \
                globalvars["namespace"], globalvars)
        else:
            oc_command("oc delete pod " + pod + " -n " + \
                globalvars["namespace"], globalvars)


def clean_rcs(rcs, globalvars):
    for rc in rcs:
        if globalvars["kubeopt"]:
            oc_command("kubectl delete rc " + rc + " -n " + \
                globalvars["namespace"], globalvars)
        else:
            oc_command("oc delete rc " + rc + " -n " + \
                globalvars["namespace"], globalvars)


def clean_users(users, globalvars):
    for user in users:
        if globalvars["kubeopt"]:
            oc_command("kubectl delete user " + user + " -n " +\
                globalvars["namespace"], globalvars)
        else:
            oc_command("oc delete user " + user + " -n " + \
                globalvars["namespace"], globalvars)


def clean_quotas(quota, globalvars):
    if globalvars["kubeopt"]:
        oc_command("kubectl delete quota " + quota + " -n " +\
            globalvars["namespace"], globalvars)
    else:
        oc_command("oc delete quota " + quota + " -n " +\
            globalvars["namespace"], globalvars)


def delete_pod(podlist,globalvars):
    namespace = globalvars["namespace"]
    
    while len(podlist) > 0 :
        if globalvars["kubeopt"]:
            getpods = oc_command("kubectl get pods --namespace " +\
                namespace, globalvars )
        else:   
            getpods = oc_command("oc get pods -n " + namespace,\
            globalvars )
        all_status = getpods.split("\n")
        all_status = filter(None, all_status)
        plist = []
        for elem in all_status[1:]:
            elemlist = elem.split()
            if elemlist[0] in podlist:
                podlist.remove(elemlist[0])
            else:
                continue
        time.sleep(5)


def find_tuning(tuningsets, name):
    for tuningset in tuningsets:
        if tuningset["name"] == name:
            return tuningset
        else:
            continue

    print "Failed to find tuningset: " + name + "\nExiting....."
    sys.exit()

def find_quota(quotaset, name):
    for quota in quotaset:
        if quota["name"] == name:
            return quota
        else:
            continue

    print "Failed to find quota : " + name + "\nExitting ......"
    sys.exit()
