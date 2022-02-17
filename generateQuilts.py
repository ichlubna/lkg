#/external/deeplens_eval-master/python2.7 eval.py obrazky v data/imgs
import os
import subprocess
import argparse
import tempfile
import shutil
import shlex
import traceback

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
    quiltResolution = [5, 9]
    videoStart = "00:00:00"
    tmpDir = ""
    doFocusing = False

    focusStep = 0.025
    focusRange = 0.4

    def parseArguments(self):
        parser = argparse.ArgumentParser(description='Converts set of 45 images into quilts with...')
        parser.add_argument('--inputDir', metavar='--inputDir', default="./", help='input directory with numbered images')
        parser.add_argument('--inputVideo', metavar='--inputVideo', default="", help='input video file - overwrites the directory')
        parser.add_argument('--outputDir', metavar='--outputDir', default="./", nargs='?', help='output directory')
        parser.add_argument('--quiltSize', metavar='--quiltSize', default="5x9", nargs='?', help='size of the quilt in images, WxH')
        parser.add_argument('--videoStart', metavar='--videoStart', default="00:00:00", nargs='?', help='where should the frames be taken from, hh:mm:ss')
        parser.add_argument('-f',  action='store_true', help='Performs focusing')
        args = parser.parse_args()
        self.inputDir = os.path.join(args.inputDir, '')
        self.inputVideo = args.inputVideo
        self.outputDir = os.path.join(args.outputDir, '')
        strQuiltRes = args.quiltSize.split('x')
        self.quiltResolution = [int(strQuiltRes[0]), int(strQuiltRes[1])]
        self.videoStart = args.videoStart
        self.doFocusing = args.f

    def analyzeInput(self):
        if(self.inputVideo):
            self.inputDir = self.tmpDir+"/videoFrames/"
            os.mkdir(self.inputDir)
            self.runBash("ffmpeg -i "+self.inputVideo+" -ss "+self.videoStart+" -frames:v 45 "+self.inputDir+"%04d.png")
        self.inputFiles = sorted(os.listdir(self.inputDir))
        if len(self.inputFiles) != self.quiltResolution[0]*self.quiltResolution[1]:
            raise Exception("Wrong number of images in the input folder, expected "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" quilt")
        self.inputExtension = os.path.splitext(self.inputFiles[0])[1]
        result = self.runBash(self.IMIdentifyPath+" -format %[fx:w]|%[fx:h] "+self.inputDir+self.inputFiles[0])
        strRes = result.stdout.split('|')
        self.imageResolution = [int(strRes[0]), int(strRes[1])]

    def runBash(self,command):
        #result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result

    def exportQuiltImage(self, inDir, outDir, name):
        self.runBash(self.IMMontagePath+" "+inDir+"*"+self.inputExtension+" -tile "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" -geometry "+str(self.imageResolution[0])+"x"+str(self.imageResolution[1])+"+0+0 "+outDir+name)
        #TODO define orientation and maybe flip + add note to help 

    def dogFocusing(self):
        testDir = tmpDir+"/dog/"
        testImagePath = testDir+"testFocus.png"
        testDogPath = testDir+"testDog.png"
        minimal = [99999999.0, 0]
        for f in range(-focusRange, focusRange, focusForceStep):
            os.mkdir(testDir)
            self.runBash(self.quiltToNativePath+" --input "+self.outputDir+"basicQuilt.png --focus "+str(f)+" --output "+testImagePath)
            self.runBash(self.IMConvertPath+" "+testImagePath+" -colorspace Gray -morphology Convolve DoG:10,0,10 -tint 0 "+testDogPath)
            result = runBash("echo $("+self.IMConvertPath+" "+testDogPath+" -resize 1x1 txt:- | grep -o -P '(?<=\().*?(?=\))' | head -n 1)")
            energy = float(result.stdout)
            if energy < minimal[0]:
                minimal = [energy, f]
            shutil.rmtree(testDir)
        return minimal[1]

    def refocusImages(self, inDir, outDir, focus):
        quiltLength = self.quiltResolution[0]*self.quiltResolution[1]
        for i in range(len(self.inputFiles)):
            imageFocus = focus*(1.0-2*i/quiltLength)*self.imageResolution[0]
            self.runBash(self.IMConvertPath+" -distort ScaleRotateTranslate '0,0 1 0 "+str(imageFocus)+",0' -virtual-pixel edge "+inDir+self.inputFiles[i]+" "+outDir+self.inputFiles[i])

    def refocusAndExport(self, outDir, name, focus):
        refocusDir = self.tmpDir+"/refocus/"
        os.mkdir(refocusDir)
        self.refocusImages(self.inputDi, refocusDir, focus)
        self.exportQuiltImage(refocusDir, outDir, name)
        shutil.rmtree(refocusDir)

    def deepFocusing(self):
        saliencyDir = self.tmpDir+"/saliency/"
        os.mkdir(saliencyDir)
        self.runBash("python "+self.gicdPath+"test.py --model GICD --input_root "+self.inputDir+" --param_path "+self.gicdPath+"gicd_ginet.pth --save_root "+saliencyDir)
        refSalDir - self.tmpDir+"/refSal/"
        saliencySumPath = self.tmpDir+"saliencySum.png"
        maximal = [-99999999.0, 0]
        for f in range(-focusRange, focusRange, focusStep):
            os.mkdir(refSalDir)
            refocusImages(saliencyDir, refSalDir, f)
            runBash(self.IMConvertPath+" "+refSalDir+"* -compose multiply -composite "+saliencySumPath)
            result = runBash("echo $("+self.IMConvertPath+" "+saliencySumPath+" -resize 1x1 txt:- | grep -o -P '(?<=\().*?(?=\))' | head -n 1)")
            energy = float(result.stdout)
            if energy > maximal[0]:
                maximal = [energy, f]
            shutil.rmtree(refSalDir)
        shutil.rmtree(saliencyDir)
        return maximal[1]

    def run(self):
        self.parseArguments()
        self.analyzeInput()
        self.exportQuiltImage(self.inputDir, self.outputDir, "basicQuilt.png")
        if(self.doFocusing):
            dogFocus = self.dogFocusing()
            self.refocusAndExport(self.outputDir, "dogRefocusedQuilt.png", dogFocus)
            deepFocus = self.deepFocusing()
            self.refocusAndExport(self.outputDir, "deepRefocusedQuilt.png", deepFocus)

    def __init__(self):
        self.tmpDir = os.path.join(tempfile.mkdtemp(), '')

    def __del__(self):
        shutil.rmtree(self.tmpDir)

c = Convertor()
try:
    c.run()
except Exception as e:
    print(e)
    print(traceback.format_exc())
