import sys
import os
import re
from collections import defaultdict

TEST_COUNT = 75

inputPath = sys.argv[1]

methods={
"angel" : {"deep" : 0.4, "dog" : 0.425},
"bricks" : {"deep" : 0.5 , "dog" : 0.005},
"buddha" : {"deep" : 0.545 , "dog" : 0.45},
"cars" : {"deep" : 0.31, "dog" : 0.485},
"cat" : {"deep" : 0.47, "dog" : 0.49},
"class" : {"deep" : 0.19 , "dog" : 0.409},
"cubes" : {"deep" : 0.5, "dog" : 0.409},
"knight" : {"deep" : 0.475, "dog" : 0.47},
"layers" : {"deep" : 0.495, "dog" : 0.47},
"rock" : {"deep" : 0.5, "dog" : 0.13},
"room" : {"deep" : 0.395, "dog" : 0.3349},
"table" : {"deep" : 0.48, "dog" : 0.475}
}

refRange={
"00":0.5,
"01"	:	0.489879	,
"02"	:	0.473684	,
"03"	:	0.453441	,
"04"	:	0.445344	,
"05"	:	0.421053	,
"06"	:	0.417004	,
"07"	:	0.425101	,
"08"	:	0.396761	,
"09"	:	0.380567	,
"10"	:	0.384615	,
"11"	:	0.384615	,
"12"	:	0.364372	,
"13"	:	0.34413	,
"14"	:	0.352227	,
"15"	:	0.368421	,
"16"	:	0.336032	,
"17"	:	0.340081	,
"18"	:	0.315789	,
"19"	:	0.311741	,
"20"	:	0.303644	,
"21"	:	0.315789	,
"22"	:	0.295547	,
"23"	:	0.283401	,
"24"	:	0.283401	,
"25"	:	0.279352	,
"26"	:	0.275304	,
"27"	:	0.279352	,
"28"	:	0.263158	,
"29"	:	0.267206	,
"31"	:	0.259109	,
"32"	:	0.251012	,
"33"	:	0.251012	,
"34"	:	0.234818	,
"35"	:	0.242915	,
"36"	:	0.246964	,
"37"	:	0.234818	,
"38"	:	0.234818	,
"39"	:	0.218624	,
"40"	:	0.226721	
}

count=0
sessionTime=0
dofResults=dict()
warpResults=dict()
warpResultsExt=dict()
rangeResults=dict()
focusResults=dict()
startFocusCount=0
endFocusCount=0

def addToSelectionDict(inDict, indexA, indexB):
    try:
        inDict[indexA][indexB] += 1
    except:
        A = int(indexB== "A")
        B = int(indexB == "B")
        inDict[indexA] = {'A' : A, 'B' : B}

def addToFocusDict(inDict, index, value):
    try:
        inDict[index]["avg"] += float(value)
        inDict[index]["min"] = min(float(value),inDict[index]["min"])
        inDict[index]["max"] = max(float(value),inDict[index]["max"])
    except:
        inDict[index] = {"avg" : float(value), "min" : float(value), "max" : float(value)}

def addToRangeDict(inDict, index, value):
    try:
        inDict[index].append(value)
    except:
        inDict[index] = [value]

def getVariance(values):
    count = len(values)
    if count == 0:
        return 0
    avg = sum(values)/count
    deviations = [(x - avg) ** 2 for x in values]
    variance = sum(deviations)/count
    return variance

def clusterRange(index):
    global startFocusCount
    global endFocusCount
    start = 0.5
    end = refRange[index]
    startValues = []
    endValues = []
    for val in rangeResults[index]:
        startDistance = abs(val-start)
        endDistance = abs(val-end)
        if startDistance < endDistance:
            startValues.append(val)
            startFocusCount += 1
        else:
            endValues.append(val)
            endFocusCount += 1
    return getVariance(rangeResults[index]), 0.5*(getVariance(startValues)+getVariance(endValues))

def rangeToTimes(ranges):
    rangeA = int(1/float(ranges[0][:1]+"."+ranges[0][1:]))
    rangeB = int(1/float(ranges[1][:1]+"."+ranges[1][1:]))
    return [str(rangeA), str(rangeB)]

for measurement in os.listdir(inputPath):
    count += 1
    f = os.path.join(inputPath, measurement)
    
    with open(f+"/times.txt") as file:
        line = file.readline()
        while line:
            sessionTime += float(line)
            line = file.readline()

    with open(f+"/selectResults.txt") as file:
        line = file.readline()
        while line:
           selection = re.search('select/(.*)/', line).group(1)
           if "Warping" in line:
                if "h.png" in line:
                    test = re.search('a0(.*)h\.png', line).group(1)
                    addToSelectionDict(warpResultsExt, test, selection)
                else:
                    test = re.search('a0(.*)\.png', line).group(1)
                    addToSelectionDict(warpResults, test, selection)
           else:
                scene = re.search('b0(.*)\.png', line).group(1)
                addToSelectionDict(dofResults, scene, selection)
           line = file.readline()
    
    with open(f+"/focusResults.txt") as file:
        line = file.readline()
        while line:
            if "Range" in line:
                test = re.search('Range(.*)\.png', line).group(1)
                val = float(line.split(' ')[1])
                if test == "39":
                    print("a"+str(val))
                addToRangeDict(rangeResults, test, val)
            else:
                test = re.search('Scene(.*)\.png', line).group(1)
                addToFocusDict(focusResults, test, line.split(' ')[1])    
            line = file.readline()

print("DoF results: \nscene nodof dof")
dof=0
nodof=0
for scene, results in dofResults.items():
    print(scene.lower() + " " + str((results['A']/count)*100) + " " + str((results['B']/count)*100))
    nodof += results['A']
    dof += results['B']
total=nodof+dof
print("Total nodof: " + str((nodof/total)*100))
print("Total dof: " + str((dof/total)*100))
print()

print("Warping results:")
print("Neigbours: \ntest upperVal lowerVal")
for rangeName, results in sorted(warpResults.items()):
    rangeNames=rangeName.split('-')
    rangeNames[0] = rangeNames[0].replace("Warping","")
    times = rangeToTimes(rangeNames)
    print(times[0] + "-" + times[1] + " " + str((results['A']/count)*100) + " " + str((results['B']/count)*100))
print()
print("Extremes: \ntest upperVal lowerVal")
for rangeName, results in sorted(warpResultsExt.items()):
    rangeNames=rangeName.split('-')
    rangeNames[0] = rangeNames[0].replace("Warping","")
    times = rangeToTimes(rangeNames)
    print(times[0] + "-" + times[1] + " " + str((results['A']/count)*100) + " " + str((results['B']/count)*100))
print()

print("Focusing results:")
print("Range: \ndistance globalvariance clusteredvariance")
for rangeName, vals in sorted(rangeResults.items()):
    variances = clusterRange(rangeName)
    rangeVal = float(rangeName[:1]+"."+rangeName[1:])
    if rangeVal == 0:
        continue
    print(str(rangeVal) + " " + str(variances[0]) + " " + str(variances[1]))
print()
print("Total focusing range clustered")
totalCount = startFocusCount+endFocusCount
print("Start: " + str((startFocusCount/totalCount)*100))
print("End: " + str((endFocusCount/totalCount)*100))
print()
print("Focusing: \nscene avg min max dog deep")
dogDiff=0
deepDiff=0
for scene, result in focusResults.items():
    print(scene+ " " + str(result["avg"]/count) + " " + str(result["min"]) + " "  + str(result["max"]) + " " + str(methods[scene]["dog"]) + " " + str(methods[scene]["deep"]))
    dogDiff += abs(methods[scene]["dog"]-result["avg"]/count)
    deepDiff += abs(methods[scene]["deep"]-result["avg"]/count)
print()
print("DoG difference: " + str(dogDiff/len(methods)))
print("Deep difference: " + str(deepDiff/len(methods)))
print()

sessionTime /= count
print("One session time: " + str(sessionTime) + " s = " + str(sessionTime/60) + " m" )
print("One test time: " + str(sessionTime/TEST_COUNT) + " s")

