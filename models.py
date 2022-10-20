from pydantic import BaseModel
from datetime import datetime
import random


class FaceModel(BaseModel):
    frame: int
    timestamp: datetime
    xyz: tuple
    is_blink: bool = False
    total_blink: int
    last_blink_duration: float = None
    head_pose: str = None


class FaceStreamModel(BaseModel):
    timestamp: datetime = None
    # Model / Logic
    is_blink: bool = False
    total_blinks: int = 0
    blink_duration: float = None
    head_pose: str = None
    # Auto increment
    frame: int = 0
    question_index: int = 0
    question_counter: int = 1
    attempt: int = 0
    counter_ok_consecutives: int = 0
    counter_ok_questions: int = 0
    blink_ok_required: int = random.randint(1, 3)

# TODO: Add new class to separate some params from FaceModel




