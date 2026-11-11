from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.curso import Curso
from app.repositories.curso import CursoRepository
from app.schemas.curso import CursoRequest, CursoResponse

curso = APIRouter(prefix="/curso", tags=["curso"])


@curso.post("/api/cursos", response_model=CursoResponse, status_code=status.HTTP_201_CREATED)
def create(request: CursoRequest, db: Session = Depends(get_db)):
    curso = CursoRepository.save(db, Curso(**request.dict()))
    return CursoResponse.from_orm(curso)


@curso.get("/api/cursos", response_model=list[CursoResponse])
def find_all(db: Session = Depends(get_db)):
    cursos = CursoRepository.find_all(db)
    return [CursoResponse.from_orm(curso) for curso in cursos]


@curso.get("/api/cursos/{id}", response_model=CursoResponse)
def find_by_id(id: int, db: Session = Depends(get_db)):
    curso = CursoRepository.find_by_id(db, id)
    if not curso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado")
    return CursoResponse.from_orm(curso)


@curso.delete("/api/cursos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(id: int, db: Session = Depends(get_db)):
    if not CursoRepository.exists_by_id(db, id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado")
    CursoRepository.delete_by_id(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@curso.put("/api/cursos/{id}", response_model=CursoResponse)
def update(id: int, request: CursoRequest, db: Session = Depends(get_db)):
    if not CursoRepository.exists_by_id(db, id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado")
    curso = CursoRepository.save(db, Curso(id=id, **request.dict()))
    return CursoResponse.from_orm(curso)
