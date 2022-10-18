from datetime import datetime
import random
import questions
import time
import cv2
from FaceAnalyzer import FaceAnalyzer

import udfs
from models import FaceModel

# import imutils

# parameters
TOTAL = 0  # Total blink time
counter_ok_questions = 0
counter_ok_consecutives = 0
limit_consecutives = 5  # Number of frames required to be counted as pass
limit_questions = 6  # Total number of questions
counter_try = 10
limit_try = 50
########################################################################################################################
frame_counter = 0
fa = FaceAnalyzer(max_nb_faces=1)
# Blinks counter
n_blinks = 0
# Prepare perclos buffers
short_perclos_buffer = []
long_perclos_buffer = []
short_perclos_ready = False
long_perclos_ready = False
# FPS processing
prev_frame_time = time.time()
curr_frame_time = time.time()


def add_txt_to_frame(video_capture, text, color=(0, 0, 255)):
    _ret, _frame = video_capture.read()
    _frame = cv2.flip(_frame, 1)
    cv2.putText(_frame, text, (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
    return _frame


cap = cv2.VideoCapture(0)
for i_questions in range(0, limit_questions):
    index_question = random.randint(0, 4)
    question = questions.question_bank(index_question)

    # Show frame with question:
    frame = add_txt_to_frame(video_capture=cap, text=question, color=(0, 0, 255))
    cv2.imshow('Liveness Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # For Each Question:
    for i_try in range(limit_try):
        frame_counter += 1
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        TOTAL_0 = TOTAL
        # DETECT LIVENESS
        curr_frame_time = time.time()
        dt = curr_frame_time - prev_frame_time
        prev_frame_time = curr_frame_time
        fps = 1 / dt

        # Process frame with FaceAnalyzer (facemesh.process)
        fa.process(frame)
        if fa.nb_faces == 1:
            ### BLINK:
            # Computes eyes opening level and blinks
            left_eye_opening, right_eye_opening, is_blink, last_blink_duration = fa.faces[0].process_eyes(frame,
                                                                                                          detect_blinks=True,
                                                                                                          blink_th=0.35,
                                                                                                          blinking_double_threshold_factor=1.05)
            # Compute perclos over two spans
            # short_perclos = fa.faces[0].compute_perclos(left_eye_opening, right_eye_opening, 5 * int(fps),
            #                                             short_perclos_buffer) * 100
            # long_perclos = fa.faces[0].compute_perclos(left_eye_opening, right_eye_opening, 60 * int(fps),
            #                                            long_perclos_buffer) * 100
            # if len(short_perclos_buffer) >= 5 * int(fps):
            #     short_perclos_ready = True
            # if len(long_perclos_buffer) >= 60 * int(fps):
            #     long_perclos_ready = True
            if is_blink:
                # print(f"Blinking : {n_blinks}")
                n_blinks += 1
            ### HEAD POSE
            head_pose = udfs.get_head_pose(cap=cap, fa=fa)
            # Return FaceModel
            face_instance = FaceModel(is_blink=is_blink,
                                      total_blink=n_blinks,
                                      last_blink_duration=last_blink_duration,
                                      frame=frame_counter,
                                      timestamp=datetime.now(),
                                      head_pose=head_pose)
        ########################################################################################################################
        TOTAL = face_instance.total_blink
        dif_blink = TOTAL - TOTAL_0
        if dif_blink > 0:
            blinks_up = 1
        else:
            blinks_up = 0
        # CHALLENGE RESULT
        challenge_res = questions.challenge_result(question, face_instance, blinks_up)
        frame = add_txt_to_frame(cap, question)
        cv2.imshow('Liveness Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if challenge_res == "pass":
            print(index_question, question, face_instance.dict())
            frame = add_txt_to_frame(cap, question + " : ok")
            cv2.imshow('Liveness Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Adding to total pass
            counter_ok_consecutives += 1
            if counter_ok_consecutives == limit_consecutives:
                counter_ok_questions += 1
                counter_try = 0
                counter_ok_consecutives = 0
                break
            else:
                continue
        elif challenge_res == "fail":
            counter_try += 1
            add_txt_to_frame(cap, question + " : fail")
        elif i_try == limit_try - 1:
            break
    if counter_ok_questions == limit_questions:
        while True:
            frame = add_txt_to_frame(cap, "LIVENESS SUCCESSFUL", color=(0, 255, 0))
            cv2.imshow('Liveness Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    elif i_try == limit_try - 1:
        while True:
            frame = add_txt_to_frame(cap, "LIVENESS FAIL")
            cv2.imshow('Liveness Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        break
    else:
        continue

cv2.destroyAllWindows()
cap.release()
