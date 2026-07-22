"""DTO pieces shared by more than one module."""

from pydantic import BaseModel, ConfigDict

# Lets a DTO be built straight from an ORM object with model_validate().
ORM_CONFIG = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Simple acknowledgement returned by endpoints with nothing else to say."""

    message: str
