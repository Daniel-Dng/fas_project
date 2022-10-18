from pydantic import BaseModel
from datetime import datetime


class FaceModel(BaseModel):
    frame: int
    timestamp: datetime
    xyz: tuple
    is_blink: bool = False
    total_blink: int
    last_blink_duration: float = None
    head_pose: str = None




