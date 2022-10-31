# Face Anti Spoofing Project

**Challenge-Response** based protocol for human verification, which can be applied in e-KYC or any auto verification system. 

The challenges include 2D head pose, random times of eye blinks, mouth opening (TODO), etc.

## Description
After **WebRTC** connection between server and client successfully formed, there are challenge commands appear in the webcam asking client to 
attempt to fulfill. After a certain number of challenges, the code will decide if the client pass the liveness test.

There are parameters to constrain or relax the verification challenge.

### Technical Specification: 
1. Python >= 3.10: `pip install -r requirements.txt`
   * WebRTC - [aiortc](https://github.com/aiortc/aiortc) via [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) Framework for connection between client and server backend

2. MongoDB server, including pymongo (MongoDB Python Client)

The project mainly relied on facial processing techniques of [MediaPipe](https://github.com/google/mediapipe) (via its secondary library [FaceAnalyzer](https://github.com/ParisNeo/FaceAnalyzer)) including:
  * Face mesh detection (& drawing)
  * Eye Blink, Mouth Opening & Head Pose calculations
  * etc.

### Running Instruction:
* For simple test of challenge-response via direct Webcam, run [face_anti_spoofing.py](face_anti_spoofing.py):
`python face_anti_spoofing.py` 

* For Streamlit WebRTC server, run [app.py](app.py): 
`streamlit run app.py`
