import uuid
from pydantic import BaseModel, Field
from typing import List


class Message(BaseModel):
    role: str
    content: str


class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
