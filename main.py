from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()


# ===================== MODELS =====================

class Patient(BaseModel):
    id: Annotated[str, Field(..., description='ID of the patient', examples=['P001'])]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(...)]
    height: Annotated[float, Field(..., gt=0, description='Height in meters')]
    weight: Annotated[float, Field(..., gt=0, description='Weight in kg')]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)
    gender: Optional[Literal['male', 'female', 'others']] = None
    height: Optional[float] = Field(default=None, gt=0)
    weight: Optional[float] = Field(default=None, gt=0)


# ===================== FILE UTILS =====================

def load_data():
    with open('patients.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data, f, indent=2)


# ===================== ROUTES =====================

@app.get("/")
def hello():
    return {'message': 'Patient Management System API'}

@app.get('/about')
def about():
    return {'message': 'A fully functional API to manage your patient records'}

@app.get('/view')
def view():
    return load_data()

@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(..., description='Patient ID')):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail='Patient not found')

@app.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description='height | weight | bmi'),
    order: str = Query('asc', description='asc | desc')
):
    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(400, f'Invalid field. Choose from {valid_fields}')
    if order not in ['asc', 'desc']:
        raise HTTPException(400, 'Order must be asc or desc')

    data = load_data()
    reverse = order == 'desc'
    return sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=reverse)


@app.post('/create')
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(400, 'Patient already exists')

    data[patient.id] = patient.model_dump(exclude=['id'])
    save_data(data)

    return JSONResponse(status_code=201, content=patient.model_dump())


@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(404, 'Patient not found')

    existing = data[patient_id]
    updates = patient_update.model_dump(exclude_unset=True)

    # safe merge
    merged = {**existing, **updates}
    merged['id'] = patient_id

    patient_obj = Patient(**merged)
    data[patient_id] = patient_obj.model_dump(exclude='id')

    save_data(data)
    return patient_obj


@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(404, 'Patient not found')

    del data[patient_id]
    save_data(data)

    return {'message': 'patient deleted'}
