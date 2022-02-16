
#images -> quilt + focus values (clankova a saliency) A quilt s FOV
#/external/deeplens_eval-master/python2.7 eval.py obrazky v data/imgs
#/external/gicd-master/python test.py --model GICD --input_root ./img/ --param_path ./gicd_ginet.pth --save_root ./imgout
#need to have installed imagemagick - montage commandline tool
import os
import subprocess
import argparse
import tempfile
import shutil
import shlex

class Convertor:
    #https://github.com/zzhanghub/gicd
    gicdPath = "external/gicd-master/test.py"
    #https://github.com/dormon/3DApps/blob/master/src/quiltToNative.cpp
    quiltToNativePath = "external/dormon/quiltToNative"
    #https://imagemagick.org/
    IMMontagePath = "montage"
    IMConvertPath = "convert"

    inputDir = ""
    outputDir = ""
    inputExtension = ""
    inputFiles = []
    imageResolution = [1920, 1080]
    quiltResolution = [5, 9]
    tmpDir = ""

    bruteForceStep = 0.025
    bruteForceRange = 0.4

    def parseArguments(self):
        parser = argparse.ArgumentParser(description='Converts set of 45 images into quilts with...')
        parser.add_argument('--inputDir', metavar='--inputDir', help='input directory with numbered images')
        parser.add_argument('--outputDir', metavar='--outputDir', default="./", nargs='?', help='output directory')
        args = parser.parse_args()
        self.inputDir = os.path.join(args.inputDir, '')
        self.outputDir = os.path.join(args.outputDir, '')

    def analyzeInput(self):
        self.inputFiles = sorted(os.listdir(self.inputDir))
        if len(self.inputFiles) != self.quiltResolution[0]*self.quiltResolution[1]:
            raise Exception("Wrong number of images in the input folder, expected "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" quilt")
        self.inputExtension = os.path.splitext(self.inputFiles[0])[1]
        result = self.runBash('identify -format %[fx:w]|%[fx:h] '+self.inputDir+self.inputFiles[0])
        self.imageResolution[0] = int(result.stdout.split('|')[0]);
        self.imageResolution[1] = int(result.stdout.split('|')[1]);

    def runBash(self,command):
        #result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result

    def exportQuiltImage(self, inDir, outDir, name):
        self.runBash(self.IMMontagePath+" "+inDir+"*"+self.inputExtension+" -tile "+str(self.quiltResolution[0])+"x"+str(self.quiltResolution[1])+" -geometry "+str(self.imageResolution[0])+"x"+str(self.imageResolution[1])+"+0+0 "+outDir+name)
        #TODO define orientation and maybe flip + add note to help 

    def bruteForceFocusing(self):
        testDir = tmpDir+"/bruteForce/"
        testImagePath = testDir+"testFocus.png"
        testDogPath = testDir+"testDog.png"
        minimal = [99999999.0, 0]
        for f in range(-bruteForceRange, bruteForceRange, bruteForceStep):
            os.mkdir(testDir)
            self.runBash(self.quiltToNativePath+" --input "+self.outputDir+"basicQuilt.png --focus "+str(f)+" --output "+testImagePath)
            self.runBash(self.IMConvertPath+" "+testImagePath+" -colorspace Gray -morphology Convolve DoG:10,0,10 -tint 0 "+testDogPath)
            result = runBash("echo $("+self.IMConvertPath+" "+testDogPath+" -resize 1x1 txt:- | grep -o -P '(?<=\().*?(?=\))' | head -n 1)")
            bluriness = float(result.stdout)
            if bluriness < minimal[0]:
                minimal = [bluriness, f]
            shutil.rmtree(testDir)
        return minimal[1]

    #def copyFiles():
    #    for f in inputFiles:
    #        shutil.copy(inputDir+"/"+f, tmpDir)

    def refocusImages(self, outDir, focus):
        quiltLength = self.quiltResolution[0]*self.quiltResolution[1]
        for i in range(len(self.inputFiles)):
            imageFocus = focus*(1.0-2*i/quiltLength)*self.imageResolution[0]
            self.runBash(self.IMConvertPath+" -distort ScaleRotateTranslate '0,0 1 0 "+str(imageFocus)+",0' -virtual-pixel edge "+self.inputDir+self.inputFiles[i]+" "+outDir+self.inputFiles[i])

    def refocusAndExport(self, outDir, name, focus):
        refocusDir = self.tmpDir+"/refocus/"
        os.mkdir(refocusDir)
        self.refocusImages(refocusDir, focus)
        self.exportQuiltImage(refocusDir, outDir, name)
        shutil.rmtree(refocusDir)

    def run(self):
        self.parseArguments()
        self.analyzeInput()
        self.exportQuiltImage(self.inputDir, self.outputDir, "basicQuilt.png")
        #bfFocus = self.bruteForceFocusing()
        self.refocusAndExport(self.outputDir, "bfRefocusedQuilt.png", 1.0)

    def __init__(self):
        self.tmpDir = os.path.join(tempfile.mkdtemp(), '')

    def __del__(self):
        shutil.rmtree(self.tmpDir)

c = Convertor()
try:
    c.run()
except Exception as e:
    print(e)
