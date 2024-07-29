# WellFiciency_physical_load_assessment
Physical Load Assessment methodologies used within the Wellficiency project

## 1. Requirements:

### Hardware:
- Movella Xsens Awinda
- Windows 10/11 system x64/x86

### Software:
- Visual Studio 2019 or above
- Visual Studio Code or Similar IDE to run/debug python scripts
- MVN Analyze Pro 2024
- DataManager LSL app ([GitHub Link](https://github.com/Augment-X/AugmentX))
- Xsens Client LSL app ([GitHub Link](https://github.com/Augment-X/XsensClient_lsl_app))
- Posture recognition hart_rt app ([GitHub Link](https://github.com/Flanders-Make-vzw/WellFiciency_physical_load_assessment))
- Physical Load Assessment app ([GitHub Link](https://github.com/Flanders-Make-vzw/WellFiciency_physical_load_assessment))
- Python 3.9 or above
- .NET 5.0 or higher

## 2. Description:
Automation of the EAWS score calculations for postural analysis using CSV files generated from posture recognition streams and Xsens sensors. The software is built up using the LSL clients developed within the AugmentX infrastructure such as “Xsens LSL app” and “DataManager App”. The physical load assessment tool also allows overlaying EAWS scores and recognized postures onto an existing recorded video of the user motions.

## 3. Action to Start Physical Load Assessment:

1. Launch MVN Analyze Pro 2024 and follow the steps to add a model and calibration ([Tutorial Link](https://www.movella.com/tutorials)).
2. In options > Network streamer, make sure that "joint angles", "euler angles" and "quaternions" are enabled.
3. Perform a recording (preferably with a camera input).
4. Once the recording is ended, export file as ".mp4" (`File > Export File`) and save it in the directory where the python scripts of the Physical load assessment and posture recognition app are located (location A).
 <p align="center">
   <img src="/resources/step3.jpg" alt="">
 </p>

4. Open `hart_rt.py` with Visual Studio Code or similar and run the code. The following should be displayed in the terminal (waiting for Xsens data to be streamed).
 
 <p align="center">
   <img src="/resources/step4.jpg" alt="">
 </p>
 
5. Open DataManager and prepare a recording session (record tab) and click “confirm”, return then to the “Main” tab.

 <p align="center">
   <img src="/resources/step5.jpg" alt="">
 </p>
 
6. Launch the Xsens LSL client app and click on “Start”.

 <p align="center">
   <img src="/resources/step6.jpg" alt="">
 </p>
 
7. Return directly to MVN Analyze Pro and play the recording.
   
8. `Hart_rt.py` should now run and the following should be displayed in the terminal.

    <p align="center">
   <img src="/resources/step8.jpg" alt="">
 </p>
 
9. Go to the Main tab of DataManager and click “List”. You should see a list of xsens streamers and the posture LSL stream (AutoDePos).

 <p align="center">
   <img src="/resources/step9.jpg" alt="">
 </p>
 
10. Click on “Uncheck all” > “Subscribe” > “Record”, the recording starts and the “record” button toggles to “stop”.

  <p align="center">
   <img src="/resources/step10.jpg" alt="">
 </p>
 
11. Stop the recording when desired and copy the “AutoDePos” csv file to location A.

 <p align="center">
   <img src="/resources/step11.jpg" alt="">
 </p>
 
12. Run `physical_load.py` by replacing the csv file name and video name.

 <p align="center">
   <img src="/resources/step12.jpg" alt="">
 </p>
 
13. A video will be generated (“output.mp4”) with the EAWS scores and recognized postures.


