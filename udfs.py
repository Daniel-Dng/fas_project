import numpy as np
import cv2


def get_face_pos(cap, fa):
    ret, frame = cap.read()
    frame_height, frame_width, frame_channel = frame.shape
    face_3d = []
    face_2d = []
    results = fa.results
    head_pose = None
    for face_landmarks in results.multi_face_landmarks:
        for idx, lm in enumerate(face_landmarks.landmark):
            if idx == 33 or idx == 263 or idx == 1 or idx == 61 or idx == 291 or idx == 199:
                # if idx == 1:
                #     nose_2d = (lm.x * frame_width, lm.y * frame_height)
                #     nose_3d = (lm.x * frame_width, lm.y * frame_height, lm.z * 3000)
                x, y = int(lm.x * frame_width), int(lm.y * frame_height)
                # Get the 2D Coordinates
                face_2d.append([x, y])
                # Get the 3D Coordinates
                face_3d.append([x, y, lm.z])
                # Convert it to the NumPy array
        face_2d = np.array(face_2d, dtype=np.float64)
        # Convert it to the NumPy array
        face_3d = np.array(face_3d, dtype=np.float64)
        # The camera matrix
        focal_length = 1 * frame_width
        cam_matrix = np.array([[focal_length, 0, frame_height / 2], [0, focal_length, frame_width / 2], [0, 0, 1]])
        # The distortion parameters
        dist_matrix = np.zeros((4, 1), dtype=np.float64)
        # Solve PnP
        success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
        # Get rotational matrix
        rmat, jac = cv2.Rodrigues(rot_vec)
        # Get angles
        angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
        # Get the y rotation degree
        x = angles[0] * 360
        y = angles[1] * 360
        z = angles[2] * 360
        # See where the user's head tilting
        if y < -15:
            head_pose = "left"
        elif y > 15:
            head_pose = "right"
        elif x < -15:
            head_pose = "down"
        elif x > 15:
            head_pose = "up"
        else:
            head_pose = "forward"
        # Display the nose direction
        # nose_3d_projection, jacobian = cv2.projectPoints(nose_3d, rot_vec, trans_vec, cam_matrix, dist_matrix)
        # p1 = (int(nose_2d[0]), int(nose_2d[1]))
        # p2 = (int(nose_2d[0] + y * 10), int(nose_2d[1] - x * 10))
        # cv2.line(frame, p1, p2, (255, 0, 0), 3)
        # drawm_facemesh(frame, fa=fa)
        # import mediapipe as mp
        # mp_drawing = mp.solutions.drawing_utils
        # drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        # mp_drawing.draw_landmarks(
        #     image=frame,
        #     landmark_list=face_landmarks,
        #     connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
        #     landmark_drawing_spec=drawing_spec,
        #     connection_drawing_spec=drawing_spec)
    return head_pose, (x, y, z)


# from FaceAnalyzer import FaceAnalyzer
# fa = FaceAnalyzer(max_nb_faces=1)


def get_head_pose_from_frame(fa, frame):
    fa.process(frame)
    frame_height, frame_width, frame_channel = frame.shape
    face_3d = []
    face_2d = []
    results = fa.results
    head_pose = None
    if fa.nb_faces == 1:
        for face_landmarks in results.multi_face_landmarks:
            for idx, lm in enumerate(face_landmarks.landmark):
                if idx == 33 or idx == 263 or idx == 1 or idx == 61 or idx == 291 or idx == 199:
                    # if idx == 1:
                    #     nose_2d = (lm.x * frame_width, lm.y * frame_height)
                    #     nose_3d = (lm.x * frame_width, lm.y * frame_height, lm.z * 3000)
                    x, y = int(lm.x * frame_width), int(lm.y * frame_height)
                    # Get the 2D Coordinates
                    face_2d.append([x, y])
                    # Get the 3D Coordinates
                    face_3d.append([x, y, lm.z])
                    # Convert it to the NumPy array
            face_2d = np.array(face_2d, dtype=np.float64)
            # Convert it to the NumPy array
            face_3d = np.array(face_3d, dtype=np.float64)
            # The camera matrix
            focal_length = 1 * frame_width
            cam_matrix = np.array([[focal_length, 0, frame_height / 2], [0, focal_length, frame_width / 2], [0, 0, 1]])
            # The distortion parameters
            dist_matrix = np.zeros((4, 1), dtype=np.float64)
            # Solve PnP
            success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
            # Get rotational matrix
            rmat, jac = cv2.Rodrigues(rot_vec)
            # Get angles
            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
            # Get the y rotation degree
            x = angles[0] * 360
            y = angles[1] * 360
            z = angles[2] * 360
            # print(x,y,z)
            # See where the user's head tilting
            if y < -10:
                head_pose = "left"
            elif y > 10:
                head_pose = "right"
            elif x < -10:
                head_pose = "down"
            elif x > 10:
                head_pose = "up"
            else:
                head_pose = "forward"
        return head_pose
