from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Nginx returns 502",
                "symptoms": "Every API request returns 502 after restarting the backend.",
                "environment": "Ubuntu server, Nginx, FastAPI running as a systemd service.",
            }
        },
    )

    title: str = Field(min_length=3, max_length=120)
    symptoms: str = Field(min_length=10, max_length=5000)
    environment: str = Field(min_length=3, max_length=1000)


class IncidentResponse(BaseModel):
    id: str
    title: str
    symptoms: str
    environment: str
    status: str
    created_at: str
    updated_at: str


class EvidenceCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source: str = Field(default="Pasted logs", min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=40000)


class MessageCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(min_length=1, max_length=10000)
