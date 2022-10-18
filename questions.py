import time


def question_bank(index):
    questions = [
        "blink eyes",
        "turn face down",
        "turn face up",
        "turn face right",
        "turn face left"]
    return questions[index]


def challenge_result(question, face_instance, blinks_up):
    if question == "turn face down":
        if face_instance.head_pose is None:
            challenge = "fail"
        elif face_instance.head_pose == "down":
            challenge = "pass"
        else:
            challenge = "fail"

    elif question == "turn face up":
        if face_instance.head_pose is None:
            challenge = "fail"
        elif face_instance.head_pose == "up":
            challenge = "pass"
        else:
            challenge = "fail"

    elif question == "turn face right":
        if face_instance.head_pose is None:
            challenge = "fail"
        elif face_instance.head_pose == "right":
            challenge = "pass"
        else:
            challenge = "fail"

    elif question == "turn face left":
        if face_instance.head_pose is None:
            challenge = "fail"
        elif face_instance.head_pose == "left":
            challenge = "pass"
        else:
            challenge = "fail"

    elif question == "blink eyes":
        if blinks_up == 1:
            challenge = "pass"
        else:
            challenge = "fail"
    return challenge
