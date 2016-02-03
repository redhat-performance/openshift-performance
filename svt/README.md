# About OSE-Cluster-Loader
This package is written in python and can be used to create an environment on top of an OpenShift installation. So, basically you can create any number of projects, each having any number of following objects -- ReplicationController, Pods, Services, etc..
Note : As of now it supports only - Pods, Replicationcontrollers, Services, and Templates.

# Sample Command

```
 $ python cluster-loader.py -f pyconfig.yaml
```
# Sample Config File
```
projects:
  - num: 2
    basename: clusterproject
    tuning: default
    templates:
      - num: 1
        file: ./content/deployment-config-1rep-template.json
        parameters:
          - IMAGE: hello-openshift
    users:
      - num: 2
        role: admin
        basename: demo
        password: demo
        userpassfile: /etc/origin/openshift-passwd
    services:
      - num: 3
        file: default
        basename: testservice
    rcs:
      - num: 2
        replicas: 5
        file: default
        basename: testrc
        image: openshift/hello-openshift:v1.0.6
    pods:
      - total: 5
      - num: 40
        image: openshift/hello-openshift:v1.0.6
        basename: hellopods
        file: default
      - num: 60
        image: rhscl/python-34-rhel7:latest
        basename: pyrhelpods
        file: default
  - num: 1
    basename: testproject

tuningsets:
  - name: default
    pods:
      stepping:
        stepsize: 5
        pause: 10 s
      rate_limit:
        delay: 250 ms
    templates:
      stepping:
        stepsize: 2
        pause: 10 s
      rate_limit:
        delay: 1 s

```

Note :
* In the "pods" section, the field - "num" stands for percentage, i.e., the number of pods will be "num" percentage of the "total" pods
* One more thing that you should note for the "pods" section is that the number of pods calculated are rounded down, when they are not exact integers.
 * Foe example : total pods = 35, num = 30, 40, 30 . In this case the pods will be 11, 12 and 11 respectively.
 * Note that the 11+12+11 = 34
* The template files defined in the "templates" section must have the parameter 'IDENTIFIER'. This will be an integer that should be used in the name of the template and in the name of the resources to ensure that no naming conflicts occur.
* The Tuning parameters have following function:
 * stepping : This feature makes sure that after each "stepsize" pod requests are submitted, they enter the "Running" state. After all the pods in the given step are Running, then there is a delay = "pause" , before the next step.
 * rate_limit : This makes sure that there is a delay of "rate_limit.delay" between each pod request submission.

```
This Config file will create the following objects :
  2 Projects : clusterproject0 , clusterproject1
   Each project has :
    2 users : demo0 , demo1  -- each with role as "admin"
    3 services : testservice0, testservice1, testservice2
    2 resplication controllers : testrc0, testrc1   -- with 5 replicas each
    5 pods : hellopods0, hellopods1, pyrhelpods0, pyrhelpods1, pyrhelpods2
  1 Project : testproject0
   This project is empty
```
# Reporting
For the current version, reporting is being handled within the package itself. It basically makes  -- "oc get"  request every 10s and records the time from a pod's submission to when the pod starts running.
The data is being collected in a file - pod_data.csv 
