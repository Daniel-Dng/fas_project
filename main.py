from streamlit_webrtc import webrtc_streamer
import av
from udfs import get_head_pose_from_frame
from datetime import datetime
import random
import questions
from models import FaceStreamModel
import threading
from FaceAnalyzer import FaceAnalyzer
import cv2
import streamlit as st
# import time
# import mediapipe as mp
import logging

logger = logging.getLogger(__name__)


# TODO:
## 1. changing limits from frames to seconds


def app_fas():
    col1, col2 = st.columns([3, 1])
    with col2:
        limit_try = st.slider("Limit Frame Attempt", min_value=0, max_value=150, step=1, value=100)
        limit_questions = st.slider("Total Challenges", min_value=1, max_value=10, step=1, value=10)
        limit_consecutives = st.slider("Number of OK Frames Required to Pass", min_value=0, max_value=10, step=1,
                                       value=5)
    face_instance = FaceStreamModel()
    lock = threading.Lock()
    fa = FaceAnalyzer(max_nb_faces=1)
    # MEDIAPIPE
    # mp_face_mesh = mp.solutions.face_mesh
    # face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    # mp_drawing = mp.solutions.drawing_utils
    # drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
    # CHALLENGE - RESPONSE Params
    # limit_consecutives = 5  # Number of frames required to be counted as pass
    # limit_questions = 10  # Total number of questions
    # limit_try = 100
    question_list = [questions.question_bank(random.randint(0, 4)) for i in range(0, limit_questions)]

    ########################################################################################################################
    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        # logger.info(img.shape) # Default shape (480, 640, 3)
        img = cv2.flip(img, 1)
        fa.process(img)
        # Control attempt for each challenge by limit number of frames
        if face_instance.attempt < limit_try:
            if face_instance.question_counter <= limit_questions:
                question = question_list[face_instance.question_index]
                cv2.putText(img,
                            f"{face_instance.question_counter}.{question}"
                            if question != 'blink eyes'
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
                cur_pose = get_head_pose_from_frame(img)
                # # Draw Face mesh
                # if fa.results.multi_face_landmarks:
                #     for face_landmarks in fa.results.multi_face_landmarks:
                #         mp_drawing.draw_landmarks(
                #             image=img,
                #             landmark_list=face_landmarks,
                #             connections=mp_face_mesh.FACEMESH_TESSELATION,
                #             landmark_drawing_spec=drawing_spec,
                #             connection_drawing_spec=drawing_spec)
                # Variables locked
                with lock:
                    face_instance.attempt += 1
                    face_instance.frame += 1
                    face_instance.head_pose = cur_pose
                    face_instance.is_blink = is_blink
                    face_instance.timestamp = datetime.now()
                    blinks_up = 0
                    if is_blink:
                        face_instance.total_blinks = face_instance.total_blinks + 1
                        logger.info(f"TOTAL BLINKS: {face_instance.total_blinks}")
                        blinks_up = 1

                    if face_instance.question_counter <= limit_questions:
                        challenge_res = questions.challenge_result(question,
                                                                   face_instance,
                                                                   blinks_up)
                        # logger.info(f'frame: {face_instance.frame}')
                        # logger.info(f'attempt: {face_instance.attempt}')
                        cv2.putText(img, f"{limit_try - face_instance.attempt}", (10, 100),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
                        # logger.info(question)
                        if challenge_res == 'pass':
                            cv2.putText(img,
                                        f"{face_instance.question_counter}.{question}: OK"
                                        if question != 'blink eyes'
                                        else f"{face_instance.question_counter}.{question} {face_instance.blink_ok_required} times: OK",
                                        (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                            face_instance.attempt = 0
                            face_instance.counter_ok_consecutives += 1
                            if (face_instance.counter_ok_consecutives == limit_consecutives) & (
                                    question != 'blink eyes'):
                                logger.info("passed")
                                face_instance.question_counter += 1
                                face_instance.question_index += 1
                                face_instance.counter_ok_consecutives = 0
                            elif (face_instance.counter_ok_consecutives == face_instance.blink_ok_required) & (
                                    question == 'blink eyes'):
                                logger.info("passed")
                                face_instance.question_counter += 1
                                face_instance.question_index += 1
                                face_instance.counter_ok_consecutives = 0
                                face_instance.blink_ok_required = random.randint(1, 3)
                            else:
                                logger.info(
                                    f"{face_instance.question_counter}.{question} ok, {face_instance.counter_ok_consecutives}")
                    else:
                        cv2.putText(img, "LIVENESS SUCCESSFUL", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1,
                                    (0, 255, 0), 2)
                        face_instance.attempt = 0
                        return av.VideoFrame.from_ndarray(img, format='bgr24')
            return av.VideoFrame.from_ndarray(img, format='bgr24')
        else:
            cv2.putText(img, "LIVENESS FAILED", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1,
                        (0, 0, 255), 2)
            return av.VideoFrame.from_ndarray(img, format='bgr24')

    with col1:
        ctx = webrtc_streamer(key="example",
                              rtc_configuration={
                                  "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                              },
                              video_frame_callback=video_frame_callback,
                              sendback_audio=False,
                              video_receiver_size=1,
                              )


def main():
    st.header("WebRTC demo")
    pages = {
        # "Real time object detection (sendrecv)": app_object_detection,
        # "Real time video transform with simple OpenCV filters (sendrecv)": app_video_filters,  # noqa: E501
        # # "Real time audio filter (sendrecv)": app_audio_filter,
        # "Delayed echo (sendrecv)": app_delayed_echo,
        # "Consuming media files on server-side and streaming it to browser (recvonly)": app_streaming,  # noqa: E501
        # "WebRTC is sendonly and images are shown via st.image() (sendonly)": app_sendonly_video,  # noqa: E501
        # # "WebRTC is sendonly and audio frames are visualized with matplotlib (sendonly)": app_sendonly_audio,  # noqa: E501
        # "Simple video and audio loopback (sendrecv)": app_loopback,
        # "Configure media constraints and HTML element styles with loopback (sendrecv)": app_media_constraints,  # noqa: E501
        # "Control the playing state programatically": app_programatically_play,
        # "Customize UI texts": app_customize_ui_texts,
        "Challenge-Response Face Verifier": app_fas
    }
    page_titles = pages.keys()
    page_title = st.sidebar.selectbox(
        "Choose the app mode",
        page_titles,
    )
    st.subheader(page_title)
    page_func = pages[page_title]
    page_func()

    logger.debug("=== Alive threads ===")
    for thread in threading.enumerate():
        if thread.is_alive():
            logger.debug(f"  {thread.name} ({thread.ident})")


if __name__ == "__main__":
    import os

    DEBUG = os.environ.get("DEBUG", "false").lower() not in ["false", "no", "0"]
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: "
               "%(message)s",
        force=True,
    )
    logger.setLevel(level=logging.DEBUG if DEBUG else logging.INFO)
    # st_webrtc_logger = logging.getLogger("streamlit_webrtc")
    # st_webrtc_logger.setLevel(logging.DEBUG)

    # fsevents_logger = logging.getLogger("fsevents")
    # fsevents_logger.setLevel(logging.WARNING)
    main()
