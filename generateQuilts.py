#/external/deeplens_eval-master/python2.7 eval.py obrazky v data/imgs
import os
import subprocess
import argparse
import tempfile
import shutil
import shlex
import traceback
import re
import math
import time

class Convertor:
    #https://github.com/zzhanghub/gicd/tree/b58759141b61ff7aec9affbbfe704a4418736ff5
    gicdPath = "external/gicd-master/"
    #https://github.com/dormon/3DApps/blob/master/src/quiltToNative.cpp
    quiltToNativePath = "external/dormon/quiltToNative"
    #https://github.com/scott89/deeplens_eval/tree/3dbc1b04ba082b3b6b1dc0d944b3d18fa542ae2c
    deepLensPath = "external/deeplens_eval-master/"
    #https://imagemagick.org/
    IMMontagePath = "montage"
    IMConvertPath = "convert"
    IMIdentifyPath = "identify"
    IMMagickPath = "magick"
    #https://www.ffmpeg.org
    FFmpegPath = "ffmpeg"

    inputDir = ""
    inputVideo = ""
    outputDir = ""
    inputExtension = ""
    inputFiles = []
    imageResolution = [1920, 1080]
    imageDepth=8
    quiltResolution = [5, 9]
    viewResolution = [0, 0]
    videoStart = "00:00:00"
    tmpDir = ""
    doFocusing = False
    verbose = False
    limitExport = False
    inputFocus = 0.0
    dofInput = [-999, -999]

    focusSteps = 100
    focusRange = 1.0

    #GETS RECALCULATED
    focusStep = 0.01

    def parseArguments(self):
        parser = argparse.ArgumentParser(description='Converts set of 45 images into quilts with...')
        parser.add_argument('--inputDir',  default="./", help='input directory with numbered images')
        parser.add_argument('--inputVideo', default="", help='input video file - overwrites the directory')
        parser.add_argument('--outputDir', default="./", nargs='?', help='output directory')
        parser.add_argument('--quiltSize', default="5x9", nargs='?', help='size of the quilt in images, WxH')
        parser.add_argument('--viewSize', default="0x0", nargs='?', help='resolution of one view in pixels, WxH')
        parser.add_argument('--videoStart', default="00:00:00", nargs='?', help='where should the frames be taken from, hh:mm:ss')
        parser.add_argument('--focus', default="0.0", type=float, nargs='?', help='creates refocused quilt to the specified distance')
        parser.add_argument('--dof', default="-999,-999", nargs='?', help='simulates DoF for the given focusing using both methods')
        parser.add_argument('-f',  action='store_true', help='performs focusing')
        parser.add_argument('-l',  action='store_true', help='will not export the autofocused quilts')
        parser.add_argument('-v',  action='store_true', help='prints results of the external commands - debugging')
        parser.add_argument('-s',  default="200", type=int, help='focus steps - density of sampling - higher = slower but more precise')
        args = parser.parse_args()
        self.inputDir = os.path.join(args.inputDir, '')
        self.inputVideo = args.inputVideo
        self.outputDir = os.path.join(args.outputDir, '')
        strQuiltRes = args.quiltSize.split('x')
        self.quiltResolution = [int(strQuiltRes[0]), int(strQuiltRes[1])]
        strDof = args.dof.split(',')
        self.dof = [float(strDof[0]), float(strDof[1])]
        self.videoStart = args.videoStart
        self.doFocusing = args.f
        self.limitExport = args.l
        self.verbose = args.v
        self.focusSteps = args.s
        self.inputFocus = args.focus
        strViewRes = args.viewSize.split('x')
        self.viewResolution = [int(strViewRes[0]), int(strViewRes[1])]

    def changeSuffix(self, name, extension):
        return os.path.splitext(name)[0]+extension

    def analyzeInput(self):
        self.focusStep = 2*self.focusRange/self.focusSteps
        resizeOption = ""
        if(self.inputVideo):
            print("Processing: "+self.inputVideo)
            self.inputDir = self.tmpDir+"videoFrames/"
            os.mkdir(self.inputDir)
            if(self.viewResolution[0] > 0):
                resizeOption = " -vf \"scale="+str(self.viewResolution[0])+"x"+str(self.viewResolution[1])+"\" "
            self.runBash(self.FFmpegPath+" -i "+self.inputVideo+" -ss "+self.videoStart+" -frames:v 45 "+resizeOption+self.inputDir+"%04d.png")
        else:
            print("Processing: "+self.inputDir)
            originalInput = self.inputDir
            inFiles = sorted(os.listdir(self.inputDir))
            self.inputDir = self.tmpDir+"frames/"
            os.mkdir(self.inputDir)
            if(self.viewResolution[0] > 0):
                resizeOption = "-resize "+str(self.viewResolution[0])+"x"+str(self.viewResolution[1])
            for f in inFiles:
               self.runBash(self.IMConvertPath+" "+originalInput+f+" "+resizeOption+" "+self.inputDir+self.changeSuffix(f, ".png"))
            self.inputFiles = sorted(os.listdir(self.inputDir))
        self.inputFiles = sorted(os.listdir(self.inputDir))
        if len(self.inputFiles) != self.quiltResolution[0]*self.quiltResolution[1]:
            raise Exception("Wrong number of images in the input folder, expected "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" quilt")
        self.inputExtension = os.path.splitext(self.inputFiles[0])[1]
        result = self.runBash(self.IMIdentifyPath+" -format %[fx:w]|%[fx:h] "+self.inputDir+self.inputFiles[0])
        strRes = result.stdout.split('|')
        self.imageResolution = [int(strRes[0]), int(strRes[1])]
        result = self.runBash(self.IMIdentifyPath+" -format %[bit-depth] "+self.inputDir+self.inputFiles[0])
        imageDepth = int(result.stdout)

    def runBash(self,command,workingDir="./"):
        result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=workingDir)
        if self.verbose:
            print(result)
            print("_____________________________________________")
        return result

    def exportQuiltImage(self, inDir, outDir, name):
        self.runBash(self.IMMontagePath+" "+inDir+"*"+self.inputExtension+" -tile "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" -geometry "+str(self.imageResolution[0])+"x"+str(self.imageResolution[1])+"+0+0 "+self.tmpDir+name)
        self.runBash(self.IMConvertPath+" "+self.tmpDir+name+" -flop -depth "+str(self.imageDepth)+" "+outDir+name)

    def averageImageEnergy(self, path):
        result = self.runBash(self.IMConvertPath+" "+path+" -resize 1x1 txt:-")
        #result = self.runBash(self.IMConvertPath+" "+path+" -resize 1x1 -format \"%[fx:int(255*r+.5)]\" info:-")
        #energy = float(result.stdout)
        energy = float(re.search(r'\((.*?)\)',result.stdout).group(1).split(",")[0])
        #energy = float(re.search(r'\((.*?)\)',result.stdout).group(1))

        return energy

    def distance(self, vec1, vec2):
        delta = [vec1[0]-vec2[0], vec1[1]-vec2[1]]
        return math.sqrt(delta[0] ** 2 + delta[1] ** 2)

    def getCenterCoordinate(self, path):
        centerImagePath = self.tmpDir+"centerImage.png"
        #maybe dilate
        result = self.runBash("convert "+path+" -threshold 40% -median 20 -type bilevel txt:-")
        pixels = result.stdout.splitlines()
        del result
        xCoords = []
        yCoords = []
        for pixel in pixels:
            if "gray(255)" in pixel:
               coords = pixel.split(":")[0].split(",")
               xCoords.append(int(coords[0]))
               yCoords.append(int(coords[1]))
        if len(xCoords) == 0 or len(yCoords) == 0:
            avg = [0,0]
        else:
            avg = [sum(xCoords) / len(xCoords), sum(yCoords) / len(yCoords)]
        closest = [[0,0],9999999]
        for i in range(0, len(xCoords)):
            coords = [xCoords[i], yCoords[i]]
            d = self.distance(avg, coords)
            if(closest[1] > d):
                closest = [coords, d]
        return closest[0]

    def getFocusMap(self, focus, outPath):
        focusPath = self.tmpDir+"focusPath/"
        os.mkdir(focusPath)
        refocusedPath = focusPath+"refocused/"
        os.mkdir(refocusedPath)
        self.refocusImages(self.inputDir, refocusedPath, focus)
        meanImagePath = focusPath+"meanImage.png"
        subtractionPath = focusPath+"subtraction/"
        os.mkdir(subtractionPath)
        self.runBash(self.IMConvertPath+" "+refocusedPath+"/* -set colorspace Gray -evaluate-sequence mean "+meanImagePath)
        for f in self.inputFiles:
            self.runBash(self.IMMagickPath+" "+meanImagePath+" "+refocusedPath+f+" -set colorspace Gray -fx \"abs(u-v)\" "+subtractionPath+f)
        self.runBash(self.IMConvertPath+" "+subtractionPath+"/* -evaluate-sequence mean "+outPath)
        shutil.rmtree(focusPath)

    def getNoBackgroundFocusMap(self, focus, outPath):
        bckgFocusPath = self.tmpDir+"bckgFocus.png"
        focusPath = self.tmpDir+"focus.png"
        rawMapPath = self.tmpDir+"rawMap.png"
        self.getFocusMap(0, bckgFocusPath)
        self.getFocusMap(focus, focusPath)
        self.runBash(self.IMMagickPath+" "+bckgFocusPath+" "+focusPath+" -fx \"(1.0-u)+v\" "+rawMapPath)
        self.runBash(self.IMConvertPath+" "+rawMapPath+" -auto-level -negate "+outPath)

    def dogFocusing(self):
        startTime = time.time()

        testDir = self.tmpDir+"dog/"
        testImagePath = testDir+"testFocus.png"
        testDogPath = testDir+"testDog.png"
        avg = 0
        values = []
        for i in range(0, self.focusSteps):
            f = -self.focusRange+i*self.focusStep
            os.mkdir(testDir)
            #subtraction method
            #testImagePathB = testDir+"testFocusB.png"
            #self.runBash(self.quiltToNativePath+" --input "+self.outputDir+"basicQuilt.png --focus "+str(f)+" --pitch 350 --output "+testImagePath)
            #self.runBash(self.quiltToNativePath+" --input "+self.outputDir+"basicQuilt.png --focus "+str(f)+" --pitch 400 --output "+testImagePathB)
            #self.runBash(self.IMConvertPath+" "+testImagePath+"  -colorspace Gray "+testImagePathB+" -colorspace Gray -compose minus -composite "+testDogPath)
            self.runBash(self.quiltToNativePath+" --input "+self.outputDir+"basicQuilt.png --focus "+str(f)+" --width "+str(self.imageResolution[0])+" --height "+str(self.imageResolution[1])+" --output "+testImagePath)
            self.runBash(self.IMConvertPath+" "+testImagePath+" -colorspace Gray -morphology Convolve DoG:10,0,10 -tint 0 "+testDogPath)
            energy = self.averageImageEnergy(testDogPath)
            shutil.rmtree(testDir)
            #print(str(f)+","+str(energy))
            values.append([f, energy])
            avg += energy

        MAX = 999999999.0
        avg /= self.focusSteps
        for i in range(len(values)):
            if(values[i][1] > avg):
                break
            values[i][1] = MAX
        for i in range(len(values)):
            j=len(values)-i-1
            if(values[j][1] > avg):
                break
            values[j][1] = MAX

        minimal = [0, MAX]
        for v in values:
            if v[1] < minimal[1]:
                minimal = v

        print("DoG scan time: "+str(time.time()-startTime))

        startTime = time.time()
        focusMapPath = self.tmpDir+"dogFocusMap.png"
        self.getNoBackgroundFocusMap(minimal[0], focusMapPath)
        focusingPoint = self.getCenterCoordinate(focusMapPath)
        print("DoG focus point time: "+str(time.time()-startTime))

        return minimal[0], focusingPoint

    def refocusImages(self, inDir, outDir, focus):
        quiltLength = self.quiltResolution[0]*self.quiltResolution[1]
        for i in range(len(self.inputFiles)):
            imageFocus = focus*(1.0-2*i/quiltLength)*self.imageResolution[0]
            self.runBash(self.IMConvertPath+" -distort ScaleRotateTranslate '0,0 1 0 "+str(-imageFocus)+",0' -virtual-pixel edge "+inDir+self.inputFiles[i]+" "+outDir+self.inputFiles[i])

    def dofImages(self, inDir, outDir, coords):
        for f in self.inputFiles:
            inputFilePath = self.deepLensPath+"data/imgs/"+f
            if(self.imageResolution[0] > 1920):
                self.runBash(self.IMConvertPath+" -geometry 1920x "+inDir+f+" "+inputFilePath)
            else:
                shutil.copy(inDir+f, inputFilePath)
            r = self.runBash("python2.7 "+"eval.py "+str(coords[0])+" "+str(coords[1]), self.deepLensPath)
            shutil.move(self.deepLensPath+"test.png", outDir+f)
            os.remove(inputFilePath)

    def refocusAndExport(self, outDir, name, focus, dofPoint=None):
        refocusDir = self.tmpDir+"refocus/"
        os.mkdir(refocusDir)
        self.refocusImages(self.inputDir, refocusDir, focus)
        self.exportQuiltImage(refocusDir, outDir, name)
        if dofPoint:
            dofDir = refocusDir+"dof/"
            os.mkdir(dofDir)
            self.dofImages(refocusDir, dofDir, dofPoint)
            self.exportQuiltImage(dofDir, outDir, "DoF"+name)
        shutil.rmtree(refocusDir)

    def saliency(self, f, saliencySumPath, saliencyDir):
        refSalDir = self.tmpDir+""+"refSal/"
        os.mkdir(refSalDir)
        self.refocusImages(saliencyDir+"/test/", refSalDir, f)
        #self.runBash(self.IMConvertPath+" "+refSalDir+"* -background None -compose Multiply -layers Flatten "+saliencySumPath)
        #self.runBash(self.IMConvertPath+" "+refSalDir+"*  -background None -evaluate-sequence Mean -layers Flatten "+saliencySumPath)
        #thresValue = self.runBash(self.IMConvertPath+" "+saliencySumPath+" -format \"%[fx:maxima*100*0.5]\" info:").stdout
        #self.runBash(self.IMConvertPath+" "+saliencySumPath+" -threshold "+thresValue+"% -type bilevel "+saliencySumThresPath)
        self.runBash(self.IMConvertPath+" "+refSalDir+"* -evaluate-sequence median "+saliencySumPath)
        energy = self.averageImageEnergy(saliencySumPath)
        shutil.rmtree(refSalDir)
        return energy

    def generateSaliencyMaps(self, saliencyDir):
        rootSalDir = self.tmpDir+"salTest/"
        refSalDir = rootSalDir+"test/"
        os.mkdir(rootSalDir)
        os.mkdir(refSalDir)
        resultingSaliencyMap = self.tmpDir+"saliencyMap.png"
        for f in self.inputFiles:
            shutil.copy(self.inputDir+f, refSalDir)
        r=self.runBash("python "+self.gicdPath+"test.py --model GICD --input_root "+rootSalDir+" --param_path "+self.gicdPath+"gicd_ginet.pth --save_root "+saliencyDir)
        shutil.rmtree(rootSalDir)


    def deepFocusing(self):
        startTime = time.time()

        saliencyDir = self.tmpDir+"saliency/"
        os.mkdir(saliencyDir)
        self.generateSaliencyMaps(saliencyDir)
        refSalDir = self.tmpDir+"refSal/"
        saliencySumPath = self.tmpDir+"saliencySum.png"
        maximal = [-99999999.0, 0]
        for i in range(0, self.focusSteps):
            f = -self.focusRange+i*self.focusStep
            energy = saliency(f, saliencySumPath)
            if energy > maximal[0]:
                maximal = [energy, f]
                shutil.copy(saliencySumPath, resultingSaliencyMap, saliencyDir)
        shutil.rmtree(saliencyDir)

        print("Deep scan time: "+str(time.time()-startTime))

        startTime = time.time()
        focusingPoint = self.getCenterCoordinate(resultingSaliencyMap)
        print("Deep focus point time: "+str(time.time()-startTime))

        return maximal[1], focusingPoint

    def generateNewDoF(self, dogFocus, deepFocus):
        resultingSaliencyMap = self.tmpDir+"saliencyMap.png"
        saliencyDir = self.tmpDir+"saliency/"
        os.mkdir(saliencyDir)
        self.generateSaliencyMaps(saliencyDir)
        self.saliency(deepFocus, resultingSaliencyMap, saliencyDir)
        dogPoint = self.getCenterCoordinate(resultingSaliencyMap)

        focusMapPath = self.tmpDir+"dogFocusMap.png"
        self.getNoBackgroundFocusMap(dogFocus, focusMapPath)
        deepPoint = self.getCenterCoordinate(focusMapPath)

        self.refocusAndExport(self.outputDir, "dogRefocusedQuilt-"+str(round(dogFocus,4))+".png", dogFocus, dogPoint)
        self.refocusAndExport(self.outputDir, "deepRefocusedQuilt-"+str(round(deepFocus,4))+".png", deepFocus, deepPoint)

    def run(self):
        self.parseArguments()
        self.analyzeInput()
        if(self.dof[0] > -100):
            self.generateNewDoF(self.dof[0], self.dof[1])
            return
        self.exportQuiltImage(self.inputDir, self.outputDir, "basicQuilt.png")
        if(self.inputFocus != 0.0):
            self.refocusAndExport(self.outputDir, "refocusedQuilt-"+str(self.inputFocus)+".png", self.inputFocus)
        if(self.doFocusing):
            dogFocus, dogPoint = self.dogFocusing()
            deepFocus, deepPoint = self.deepFocusing()
            print("DoG focus: "+str(dogFocus)+", focus point: "+str(dogPoint))
            print("Deep focus: "+str(deepFocus)+", focus point: "+str(deepPoint))
            if not self.limitExport:
                self.refocusAndExport(self.outputDir, "dogRefocusedQuilt-"+str(round(dogFocus,4))+".png", dogFocus, dogPoint)
                self.refocusAndExport(self.outputDir, "deepRefocusedQuilt-"+str(round(deepFocus,4))+".png", deepFocus, deepPoint)

    def __init__(self):
        self.tmpDir = os.path.join(tempfile.mkdtemp(), '')

    def __del__(self):
        shutil.rmtree(self.tmpDir)
        return

c = Convertor()
try:
    c.run()
except Exception as e:
    print(e)
    print(traceback.format_exc())

