#/external/deeplens_eval-master/python2.7 eval.py obrazky v data/imgs
import os
import subprocess
import argparse
import tempfile
import shutil
import shlex
import traceback
import re

class Convertor:
    #https://github.com/zzhanghub/gicd
    gicdPath = "external/gicd-master/"
    #https://github.com/dormon/3DApps/blob/master/src/quiltToNative.cpp
    quiltToNativePath = "external/dormon/quiltToNative"
    #https://imagemagick.org/
    IMMontagePath = "montage"
    IMConvertPath = "convert"
    IMIdentifyPath = "identify"

    inputDir = ""
    inputVideo = ""
    outputDir = ""
    inputExtension = ""
    inputFiles = []
    imageResolution = [1920, 1080]
    imageDepth=8
    quiltResolution = [5, 9]
    videoStart = "00:00:00"
    tmpDir = ""
    doFocusing = False
    inputFocus = 0.0

    focusSteps = 10
    focusRange = 0.4
    focusStep = 0.01

    def parseArguments(self):
        parser = argparse.ArgumentParser(description='Converts set of 45 images into quilts with...')
        parser.add_argument('--inputDir',  default="./", help='input directory with numbered images')
        parser.add_argument('--inputVideo', default="", help='input video file - overwrites the directory')
        parser.add_argument('--outputDir', default="./", nargs='?', help='output directory')
        parser.add_argument('--quiltSize', default="5x9", nargs='?', help='size of the quilt in images, WxH')
        parser.add_argument('--videoStart', default="00:00:00", nargs='?', help='where should the frames be taken from, hh:mm:ss')
        parser.add_argument('--focus', default="0.0", type=float, nargs='?', help='creates refocused quilt to the specified distance')
        parser.add_argument('-f',  action='store_true', help='performs focusing')
        args = parser.parse_args()
        self.inputDir = os.path.join(args.inputDir, '')
        self.inputVideo = args.inputVideo
        self.outputDir = os.path.join(args.outputDir, '')
        strQuiltRes = args.quiltSize.split('x')
        self.quiltResolution = [int(strQuiltRes[0]), int(strQuiltRes[1])]
        self.videoStart = args.videoStart
        self.doFocusing = args.f
        self.inputFocus = args.focus

    def analyzeInput(self):
        if(self.inputVideo):
            self.inputDir = self.tmpDir+"videoFrames/"
            os.mkdir(self.inputDir)
            self.runBash("ffmpeg -i "+self.inputVideo+" -ss "+self.videoStart+" -frames:v 45 "+self.inputDir+"%04d.png")
        self.inputFiles = sorted(os.listdir(self.inputDir))
        if len(self.inputFiles) != self.quiltResolution[0]*self.quiltResolution[1]:
            raise Exception("Wrong number of images in the input folder, expected "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" quilt")
        self.inputExtension = os.path.splitext(self.inputFiles[0])[1]
        result = self.runBash(self.IMIdentifyPath+" -format %[fx:w]|%[fx:h] "+self.inputDir+self.inputFiles[0])
        strRes = result.stdout.split('|')
        self.imageResolution = [int(strRes[0]), int(strRes[1])]
        result = self.runBash(self.IMIdentifyPath+" -format %[bit-depth] "+self.inputDir+self.inputFiles[0])
        imageDepth = int(result.stdout)

    def runBash(self,command):
        result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result

    def exportQuiltImage(self, inDir, outDir, name):
        self.runBash(self.IMMontagePath+" "+inDir+"*"+self.inputExtension+" -tile "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" -geometry "+str(self.imageResolution[0])+"x"+str(self.imageResolution[1])+"+0+0 "+self.tmpDir+name)
        self.runBash(self.IMConvertPath+" "+self.tmpDir+name+" -flop -depth "+str(self.imageDepth)+" "+outDir+name)

    def averageImageEnergy(self,path):
        result = self.runBash(self.IMConvertPath+" "+path+" -resize 1x1 txt:-")
        energy = float(re.search(r'\((.*?)\)',result.stdout).group(1))
        return energy

    def dogFocusing(self):
        testDir = self.tmpDir+"dog/"
        testImagePath = testDir+"testFocus.png"
        testDogPath = testDir+"testDog.png"
        minimal = [99999999.0, 0]
        for i in range(0, self.focusSteps):
            f = -self.focusRange+i*self.focusStep
            os.mkdir(testDir)
            self.runBash(self.quiltToNativePath+" --input "+self.outputDir+"basicQuilt.png --focus "+str(f)+" --output "+testImagePath)
            self.runBash(self.IMConvertPath+" "+testImagePath+" -colorspace Gray -morphology Convolve DoG:10,0,10 -tint 0 "+testDogPath)
            energy = self.averageImageEnergy(testDogPath)
            if energy < minimal[0]:
                minimal = [energy, f]
            shutil.rmtree(testDir)
        return minimal[1]

    def refocusImages(self, inDir, outDir, focus):
        quiltLength = self.quiltResolution[0]*self.quiltResolution[1]
        for i in range(len(self.inputFiles)):
            imageFocus = focus*(1.0-2*i/quiltLength)*self.imageResolution[0]
            self.runBash(self.IMConvertPath+" -distort ScaleRotateTranslate '0,0 1 0 "+str(-imageFocus)+",0' -virtual-pixel edge "+inDir+self.inputFiles[i]+" "+outDir+self.inputFiles[i])

    def refocusAndExport(self, outDir, name, focus):
        refocusDir = self.tmpDir+"refocus/"
        os.mkdir(refocusDir)
        self.refocusImages(self.inputDir, refocusDir, focus)
        self.exportQuiltImage(refocusDir, outDir, name)
        shutil.rmtree(refocusDir)

    def deepFocusing(self):
        saliencyDir = self.tmpDir+"saliency/"
        os.mkdir(saliencyDir)
        inSalDir = self.tmpDir+"inSalDir/"
        os.mkdir(inSalDir)
        inSalTestDir = inSalDir+"test/"
        saliencyTestDir = saliencyDir+"test/"
        os.mkdir(inSalTestDir)
        for f in self.inputFiles:
            shutil.copy(self.inputDir+f, inSalTestDir)
        r=self.runBash("python "+self.gicdPath+"test.py --model GICD --input_root "+inSalDir+" --param_path "+self.gicdPath+"gicd_ginet.pth --save_root "+saliencyDir)
        refSalDir = self.tmpDir+"refSal/"
        saliencySumPath = self.tmpDir+"saliencySum.png"
        maximal = [-99999999.0, 0]
        for i in range(0, self.focusSteps):
            f = -self.focusRange+i*self.focusStep
            os.mkdir(refSalDir)
            self.refocusImages(saliencyTestDir, refSalDir, f)
            self.runBash(self.IMConvertPath+" "+refSalDir+"* -compose multiply -composite "+saliencySumPath)
            energy = self.averageImageEnergy(saliencySumPath)
            if energy > maximal[0]:
                maximal = [energy, f]
            shutil.rmtree(refSalDir)
        shutil.rmtree(saliencyDir)
        return maximal[1]

    def run(self):
        self.parseArguments()
        self.analyzeInput()
        self.exportQuiltImage(self.inputDir, self.outputDir, "basicQuilt.png")
        if(self.inputFocus != 0.0):
            self.refocusAndExport(self.outputDir, "refocusedQuilt-"+str(self.inputFocus)+".png", self.inputFocus)
        if(self.doFocusing):
            dogFocus = round(self.dogFocusing(),4)
            self.refocusAndExport(self.outputDir, "dogRefocusedQuilt-"+str(dogFocus)+".png", dogFocus)
            deepFocus = round(self.deepFocusing(),4)
            self.refocusAndExport(self.outputDir, "deepRefocusedQuilt-"+str(deepFocus)+".png", deepFocus)

    def __init__(self):
        self.tmpDir = os.path.join(tempfile.mkdtemp(), '')
        self.focusStep = 2*self.focusRange/self.focusSteps

    def __del__(self):
        shutil.rmtree(self.tmpDir)

c = Convertor()
try:
    c.run()
except Exception as e:
    print(e)
    print(traceback.format_exc())
