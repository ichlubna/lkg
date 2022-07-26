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

count=0
sessionTime=0
dofResults=dict()
warpResults=dict()
warpResultsExt=dict()
rangeResults=dict()
focusResults=dict()

def addToSelectionDict(inDict, indexA, indexB):
    try:
        inDict[indexA][indexB] += 1
    except:
        A = int(indexB== "A")
        B = int(indexB == "B")
        inDict[indexA] = {'A' : A, 'B' : B}

def addToFocusDict(inDict, index, value):
    try:
        inDict[index] += float(value)
    except:
        inDict[index] = float(value)

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
                addToFocusDict(rangeResults, test, line.split(' ')[1])
            else:
                test = re.search('Scene(.*)\.png', line).group(1)
                addToFocusDict(focusResults, test, line.split(' ')[1])    
            line = file.readline()

print("DoF results: \nscene,nodof,dof")
dof=0
nodof=0
for scene, results in dofResults.items():
    print(scene + "," + str(results['A']) + "," + str(results['B']))
    nodof += results['A']
    dof += results['B']
print("Total nodof: " + str(nodof))
print("Total dof: " + str(dof))
print()

print("Warping results:")
print("Neigbours: \nupper,lower, upperVal, lowerVal")
for rangeName, results in warpResults.items():
    rangeNames=rangeName.split('-')
    print(rangeNames[0].replace("Warping","") + "," + rangeNames[1] + "," + str(results['A']) + "," + str(results['B']))
print()
print("Extremes: \nupper,lower, upperVal, lowerVal")
for rangeName, results in warpResultsExt.items():
    rangeNames=rangeName.split('-')
    print(rangeNames[0].replace("Warping","") + "," + rangeNames[1] + "," + str(results['A']) + "," + str(results['B']))
print()

print("Focusing results:")
print("Range: \ndistance,value")
for rangeName, result in rangeResults.items():
    print(rangeName + "," + str(result/count))
print()
print("Focusing: \nscene, value")
dogDiff=0
deepDiff=0
for scene, result in focusResults.items():
    print(scene+ "," + str(result/count))
    dogDiff += abs(methods[scene]["dog"]-result/count)
    deepDiff += abs(methods[scene]["deep"]-result/count)
print()
print("DoG difference: " + str(dogDiff/len(methods)))
print("Deep difference: " + str(deepDiff/len(methods)))
print()

sessionTime /= count
print("One session time: " + str(sessionTime) + " s = " + str(sessionTime/60) + " m" )
print("One test time: " + str(sessionTime/TEST_COUNT) + " s")

