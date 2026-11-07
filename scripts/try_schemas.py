from pydantic import ValidationError

from app.schemas import TriageResult

ok = TriageResult(label="Bug", confidence=0.85, suggested_reply="Gracias, parece un bug.",needs_human=False)
print(ok.model_dump_json(indent=2))

try:
    TriageResult(label="Question", confidence=1.5, suggested_reply="x", needs_human=False)
except ValidationError as e:
    print(e)  # debe reportar 2 errores: label inválido y confidence > 1