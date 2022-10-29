from datetime import datetime
import random
import questions
import time
import cv2
from FaceAnalyzer import FaceAnalyzer
import udfs
from models import SimpleFaceModel
# import imutils

# parameters
TOTAL = 0  # Total blink time
counter_ok_questions = 0
counter_ok_consecutives = 0
limit_consecutives = 3  # Number of frames required to be counted as pass
limit_questions = 10  # Total number of questions
counter_try = 0
limit_try = 50  # Number of frames allowed to try in each question
# blink_ok_required = 2

########################################################################################################################
frame_counter = 0
fa = FaceAnalyzer(max_nb_faces=1)
# Blinks counter
n_blinks = 0
# Prepare perclos buffers
# short_perclos_buffer = []
# long_perclos_buffer = []
# short_perclos_ready = False
# long_perclos_ready = False
# FPS processing
prev_frame_time = time.time()
curr_frame_time = time.time()


def add_txt_to_frame(video_capture, text, color=(0, 0, 255)):
    _ret, _frame = video_capture.read()
    _frame = cv2.flip(_frame, 1)
    cv2.putText(_frame, text, (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
    return _frame


cap = cv2.VideoCapture(0)
output_size = (600, 480)
out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 7, output_size)

for i_questions in range(0, limit_questions):
    index_question = random.randint(0, 4)
    blink_ok_required = random.randint(1, 3)
    question = questions.question_bank(index_question)

    # Show frame with question:
    frame = add_txt_to_frame(video_capture=cap, text=question, color=(0, 0, 255))
    cv2.imshow('Liveness Detection', frame)
    out.write(cv2.resize(frame, output_size))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # For Each Question:
    for i_try in range(limit_try):
        frame_counter += 1
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        TOTAL_0 = TOTAL
        ####### DETECT LIVENESS
        curr_frame_time = time.time()
        dt = curr_frame_time - prev_frame_time
        prev_frame_time = curr_frame_time
        fps = 1 / dt
        # print(f'FPS: {fps}')
        # print(f'Blink Required: {blink_ok_required}')
        # Process frame with FaceAnalyzer (facemesh.process)
        fa.process(frame)
        if fa.nb_faces == 1:
            ### BLINK:
            # Computes eyes opening level and blinks
            left_eye_opening, right_eye_opening, is_blink, last_blink_duration = fa.faces[0].process_eyes(frame,
                                                                                                          detect_blinks=True,
                                                                                                          blink_th=0.35,
                                                                                                          blinking_double_threshold_factor=1.05)
            if is_blink:
                # print(f"Blinking : {n_blinks}")
                n_blinks += 1
            ### HEAD POSE
            head_pose, xyz = udfs.get_face_pos(cap=cap, fa=fa)
            # Return FaceModel
            face_instance = SimpleFaceModel(is_blink=is_blink,
                                            total_blink=n_blinks,
                                            xyz=xyz,
                                            last_blink_duration=round(last_blink_duration, 4),
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
        out.write(cv2.resize(frame, output_size))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if challenge_res == "pass":
            # print(index_question, question, face_instance.dict())
            frame = add_txt_to_frame(cap, question + " : ok")
            cv2.imshow('Liveness Detection', frame)
            out.write(cv2.resize(frame, output_size))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Adding to total pass
            counter_ok_consecutives += 1

            # Demand the number of OK frames equals number of frame set in limit_consecutives
            if (counter_ok_consecutives == limit_consecutives) & (question != 'blink eyes'):
                counter_ok_questions += 1
                counter_try = 0
                counter_ok_consecutives = 0
                break
            # Demand blink exactly twice
            elif (question == 'blink eyes') & (counter_ok_consecutives == blink_ok_required):
                # print("BLINKKK")
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
            out.write(cv2.resize(frame, output_size))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    elif i_try == limit_try - 1:
        while True:
            frame = add_txt_to_frame(cap, "LIVENESS FAIL")
            cv2.imshow('Liveness Detection', frame)
            out.write(cv2.resize(frame, output_size))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        break
    else:
        continue

cv2.destroyAllWindows()
cap.release()
out.release()
