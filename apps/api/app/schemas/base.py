from pydantic import BaseModel, ConfigDict


# Base schema used by API request and response models.
class APIModel(BaseModel):
    # Allows Pydantic models to read data directly from SQLAlchemy objects.
    model_config = ConfigDict(from_attributes=True)