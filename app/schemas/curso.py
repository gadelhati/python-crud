from pydantic import BaseModel, ConfigDict


class CursoBase(BaseModel):
    titulo: str
    descricao: str
    carga_horaria: int
    qtd_exercicios: int


class CursoRequest(CursoBase): ...


class CursoResponse(CursoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
