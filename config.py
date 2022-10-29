from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Face Anti-Spoofing"
    DATA_DIR: str
    RECORDER_DIR: str
    # MongoDB
    MONGO_URL: str = 'mongodb://localhost:27017'
    MONGO_DB: str = 'local'
    FAS_SESSION_COLLECTION: str
    FAS_FACE_COLLECTION: str
    # Frontend Element
    FE_ELEMENT_KEY: str = 'fas'

    class Config:
        env_file = ".env"


settings = Settings()
