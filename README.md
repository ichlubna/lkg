# LKG Experiments
Scripts and experimental tools for Looking Glass Holographic display

## generateQuilts.py
Generates quilts from input files. Is used for automatic focusing experiments.

## data/LKGCrashDemo.blend
Demo scene with scripted environment for LKG rendering in Blender

## processData.py
Script to process the measured data from the Autofocusing User Study renderer below.

## Scene warping script for Blender
Warps the scene while keeping the same relative positions of vertices from the camera view. Reduces the depth range of the scene to widen the focusing range on LKG.
[Available here](https://github.com/ichlubna/blenderScripts/blob/master/MISC/scaleOptical.py)

## Additional LKG tools (renderers, convertors...) 
* 3D Apps toolkit - [Build instructions](https://github.com/dormon/3DApps)
  * [Quilt Autofocusing User Study Renderer](https://github.com/dormon/3DApps/blob/master/src/renderHoloFocusStudy.cpp)
  * [3D Model Renderer](https://github.com/dormon/3DApps/blob/master/src/renderHoloModel.cpp)
  * [Quilt Renderer](https://github.com/dormon/3DApps/blob/master/src/renderHoloFocus.cpp)
  * [Camera Distortions User Study](https://github.com/dormon/3DApps/blob/master/src/renderHoloUserStudy.cpp) - paper TBD
  * [Quilt Detector](https://github.com/dormon/3DApps/blob/master/src/quiltDetector.cpp) - paper TBD
  * [Quilt to Native LKG Format Convertor](https://github.com/dormon/3DApps/blob/master/src/quiltToNative.cpp)
  * [Looking Glass Device Calibration Fetch Tool/Driver](https://github.com/dormon/3DApps/blob/master/src/holoCalibration.cpp)
* [Blender LF camera generator (LKG support)](https://github.com/ichlubna/blenderScripts/blob/master/LF/cameras.py)
