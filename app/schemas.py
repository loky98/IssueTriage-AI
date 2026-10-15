"""Esquemas de entrada y salida del agente."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Label = Literal["Bug", "Docs", "Enhancement", "Usage Question"]


class DuplicateRef(BaseModel):
    number: int = Field(description="Número del issue similar o duplicado")
    url: str
    reason: str = Field(description="Por qué se considera similar, en una frase")


class DocRef(BaseModel):
    section: str = Field(description="Sección de la documentación de pandas")
    url: str


class TriageResult(BaseModel):
    reasoning: str = Field(description="Briefly compare the user's expected behavior with the actual "
                                    "result of running their code, before choosing the label")
    label: Label = Field(description="Clasificación del issue")
    confidence: float = Field(ge=0, le=1, description="Confidence as a number between 0 and 1 "
                                                    "(e.g. 0.85), not a percentage")
    duplicates: list[DuplicateRef] = Field(default_factory=list)
    doc_refs: list[DocRef] = Field(default_factory=list)
    suggested_reply: str = Field(description="Respuesta sugerida para el autor del issue")
    needs_human: bool = Field(description="True si un mantenedor debe revisarlo")

    @field_validator("confidence", mode="before")
    @classmethod
    def percent_to_fraction(cls, v):
        """Si el LLM responde un porcentaje (ej. 95), lo convierte a 0.95."""
        if isinstance(v, (int, float)) and 1 < v <= 100:
            return v / 100
        return v


class IssueInput(BaseModel):
    title: str = Field(min_length=3)
    body: str = ""