# Face Anti Spoofing Project

Challenge-Response based protocol for human facial verification 

Challenges including head pose detection, eye blink detection, mouth opening detection, etc.

## Technical Specification:
* Python >= 3.10: mainly relied on [MediaPipe](https://github.com/google/mediapipe) based library [FaceAnalyzer](https://github.com/ParisNeo/FaceAnalyzer) used for face processing including:
  * Face mesh detection
  * Eye Blink, Mouth Opening & Head Pose calculations
  * etc.


* WebRTC - [aiortc](https://github.com/aiortc/aiortc) via [FastAPI](https://github.com/tiangolo/fastapi) Framework for connection between client and server backend

## Description
After WebRTC connection successfully formed, there are challenge commands appear in the webcam asking client to 
attempt to fulfill. After a certain of try numbers, the code will decide if the client pass the liveness test.

### Instruction:
* For simple test of challenge-response:`python face_anti_spoofing.py` 

## TODO:
* FastAPI, WebRTC Communication