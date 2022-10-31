from pydantic import BaseModel, Field
from datetime import datetime
import random
from bson import ObjectId
from config import settings
# import motor.motor_asyncio
from pymongo import MongoClient

# MongoDB
client = MongoClient(settings.MONGO_URL)
db = client[settings.MONGO_DB]


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class CustomBaseModel(BaseModel):
    _id: PyObjectId = Field(default_factory=PyObjectId)

    @property
    def mongo_collection(self) -> str:
        return ''

    def create_mongo_instance(self):
        new_instance = db[self.mongo_collection].insert_one(self.dict(exclude_none=True))
        created_instance = db[self.mongo_collection].find_one({"_id": new_instance.inserted_id})
        created_instance['_id'] = str(created_instance['_id'])
        return created_instance


class SessionModel(CustomBaseModel):
    session_id: str
    start_dttm: datetime  # = datetime.now()
    video_location: str = None
    # Adjustable Params
    record: bool
    draw_face: bool
    limit_questions: int
    limit_to_fail: int
    limit_to_pass: int
    question_list: list
    # Liveness Check Decision
    liveness: int = None
    face_list: list = None

    @property
    def mongo_collection(self):
        return settings.FAS_SESSION_COLLECTION


class FaceModel(CustomBaseModel):
    session_id: str
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
    consecutive_ok_counter: int = 0
    blink_ok_required: int = random.randint(1, 3)

    @property
    def mongo_collection(self):
        return settings.FAS_FACE_COLLECTION


class SimpleFaceModel(BaseModel):
    frame: int
    timestamp: datetime
    xyz: tuple
    is_blink: bool = False
    total_blink: int
    last_blink_duration: float = None
    head_pose: str = None
# TODO: Add new class to separate some params from FaceModel
