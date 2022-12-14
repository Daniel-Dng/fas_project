from streamlit_webrtc import webrtc_streamer
import av
from udfs import get_head_pose_from_frame
from datetime import datetime
import random
import questions
from models import FaceModel, SessionModel
import threading
from FaceAnalyzer import FaceAnalyzer
import cv2
import streamlit as st
import uuid
import mediapipe as mp
import logging
from aiortc.contrib.media import MediaRecorder
from config import settings

RECORDER_DIR = settings.RECORDER_DIR
FE_ELEMENT_KEY = settings.FE_ELEMENT_KEY

logger = logging.getLogger(__name__)
lock = threading.Lock()


# TODO:
## 1. changing limits from frames to seconds
## 2. Async Streamlit: https://gist.github.com/wfng92/0cc6673e9ce4e8b880e6a38c134ed0cf
## 3. optimize speed (when draw)

def app_fas():
    col1, col2 = st.columns([3, 1])
    with col2:
        # Challenge Params
        record = st.checkbox("Record Video", value=False)
        draw_face = st.checkbox("Draw Face Mesh", value=False)
        limit_questions = st.slider("Total Challenges", min_value=1, max_value=10, step=1, value=10)
        limit_to_fail = st.slider("Number of Frames to Fail", min_value=0, max_value=150, step=1, value=100)
        limit_to_pass = st.slider("Number of Frames Required to Pass", min_value=0, max_value=10, step=1, value=5)
    # Random Question List
    question_list = [questions.question_bank(random.randint(0, 4)) for i in range(0, limit_questions)]
    face_list = []
    # Initialize Classes
    session_id = str(uuid.uuid4())
    session_instance = SessionModel(session_id=session_id,
                                    start_dttm=datetime.now(),
                                    video_location=f"{RECORDER_DIR}/{session_id}",
                                    record=record,
                                    draw_face=draw_face,
                                    limit_questions=limit_questions,
                                    limit_to_fail=limit_to_fail,
                                    limit_to_pass=limit_to_pass,
                                    question_list=question_list,
                                    )
    face_instance = FaceModel(session_id=session_id)
    fa = FaceAnalyzer(max_nb_faces=1)
    # MEDIAPIPE
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils
    drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
########################################################################################################################

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        # logger.info(img.shape) # Default shape (480, 640, 3)
        img = cv2.flip(img, 1)
        # # Write Frames to Images
        # file_name = f"screenshots/video_frame_{face_instance.frame}.png"
        # cv2.imwrite(filename=file_name, img=img)
        # # Save all Face Instances
        face_instance.create_mongo_instance()
        with lock:
            face_instance.frame += 1
        face_list.append(face_instance.dict())
        # Process with FaceAnalyzer
        fa.process(img)
        # Control attempt for each challenge by limit number of frames
        if face_instance.attempt < limit_to_fail:
            # Constrain by limit for number of questions
            if face_instance.question_counter <= limit_questions:
                question = question_list[face_instance.question_index]
                cv2.putText(img,
                            f"{face_instance.question_counter}.{question}" if question != 'blink eyes'
                            else f"{face_instance.question_counter}.{question} {face_instance.blink_ok_required} times",
                            (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            # In case at least a face detected by MediaPipe
            if fa.nb_faces == 1:
                # Detect Eye Blink
                left_eye_opening, right_eye_opening, is_blink, last_blink_duration = fa.faces[0].process_eyes(img,
                                                                                                              detect_blinks=True,
                                                                                                              blink_th=0.35,
                                                                                                              blinking_double_threshold_factor=1.05)
                # Detect Head Pose
                cur_pose = get_head_pose_from_frame(fa, img)
                # Draw Face mesh, if selected
                if session_instance.draw_face:
                    if fa.results.multi_face_landmarks:
                        for face_landmarks in fa.results.multi_face_landmarks:
                            mp_drawing.draw_landmarks(
                                image=img,
                                landmark_list=face_landmarks,
                                connections=mp_face_mesh.FACEMESH_TESSELATION,
                                landmark_drawing_spec=drawing_spec,
                                connection_drawing_spec=drawing_spec)
                # Variables locked with thread
                with lock:
                    face_instance.attempt += 1
                    face_instance.head_pose = cur_pose
                    face_instance.is_blink = is_blink
                    blinks_up = 0
                    if is_blink:
                        face_instance.total_blinks = face_instance.total_blinks + 1
                        logger.info(f"TOTAL BLINKS: {face_instance.total_blinks}")
                        blinks_up = 1
                    if face_instance.question_counter <= limit_questions:
                        challenge_res = questions.challenge_result(question, face_instance, blinks_up)
                        cv2.putText(img, f"{limit_to_fail - face_instance.attempt}", (10, 100),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
                        if challenge_res == 'pass':
                            cv2.putText(img, f"{face_instance.question_counter}.{question}: OK"
                                        if question != 'blink eyes'
                                        else f"{face_instance.question_counter}.{question} {face_instance.blink_ok_required} times: OK",
                                        (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                            face_instance.attempt = 0
                            face_instance.consecutive_ok_counter += 1
                            # Check if OK for enough frames (limit_to_pass)
                            if (face_instance.consecutive_ok_counter == limit_to_pass) & (
                                    question != 'blink eyes'):
                                # Flow for all questions, except eye blink
                                logger.info("passed")
                                face_instance.question_counter += 1
                                face_instance.question_index += 1
                                face_instance.consecutive_ok_counter = 0
                            elif (face_instance.consecutive_ok_counter == face_instance.blink_ok_required) & (
                                    question == 'blink eyes'):
                                # Flow for eye blink
                                logger.info("passed")
                                face_instance.question_counter += 1
                                face_instance.question_index += 1
                                face_instance.consecutive_ok_counter = 0
                                face_instance.blink_ok_required = random.randint(1, 3)
                            else:
                                # Counting OK Frames
                                logger.info(
                                    f"{face_instance.question_counter}.{question} ok, {face_instance.consecutive_ok_counter}")
                    else:
                        # Liveness successful, all challenges passed
                        cv2.putText(img, "LIVENESS SUCCESSFUL", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        face_instance.attempt = 0
                        session_instance.liveness = 1
                        return av.VideoFrame.from_ndarray(img, format='bgr24')
            return av.VideoFrame.from_ndarray(img, format='bgr24')
        else:
            cv2.putText(img, "LIVENESS FAILED", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            session_instance.liveness = 0
            return av.VideoFrame.from_ndarray(img, format='bgr24')

    def on_vid_ended():
        # session_instance.face_list = face_list
        session_instance.video_location = f"{RECORDER_DIR}/{session_id}" if record else None
        session_instance.create_mongo_instance()

    def out_recorder_factory() -> MediaRecorder:
        return MediaRecorder(f"{RECORDER_DIR}/test_output.flv", format="flv")

    def in_recorder_factory() -> MediaRecorder:
        return MediaRecorder(f"{RECORDER_DIR}/test_input.flv", format="flv")

    with col1:
        if record:
            webrtc_streamer(key=FE_ELEMENT_KEY,
                            video_frame_callback=video_frame_callback,
                            sendback_audio=False,
                            video_receiver_size=1,
                            out_recorder_factory=out_recorder_factory,
                            in_recorder_factory=in_recorder_factory,
                            on_video_ended=on_vid_ended,
                            )
        else:
            webrtc_streamer(key=FE_ELEMENT_KEY,
                            video_frame_callback=video_frame_callback,
                            sendback_audio=False,
                            video_receiver_size=1,
                            on_video_ended=on_vid_ended,
                            )


def main():
    st.header("WebRTC demo")
    fas_page = "Challenge-Response Face Verifier (sendrecv)"
    # loopback_page = "Simple video loopback"
    app_mode = st.sidebar.selectbox(
        "Choose the app mode",
        [
            fas_page,
            # loopback_page,
        ],
    )
    st.subheader(app_mode)
    if app_mode == fas_page:
        app_fas()
    # elif app_mode == loopback_page:
    #     app_loopback()

    # logger.debug("=== Alive threads ===")
    # for thread in threading.enumerate():
    #     if thread.is_alive():
    #         logger.debug(f"  {thread.name} ({thread.ident})")


if __name__ == "__main__":
    import os
    DEBUG = os.environ.get("DEBUG", "false").lower() not in ["false", "no", "0"]
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: "
               "%(message)s",
        force=True,
    )
    logger.setLevel(level=logging.DEBUG if DEBUG else logging.INFO)
    main()
