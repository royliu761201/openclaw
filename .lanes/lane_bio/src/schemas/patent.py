from pydantic import BaseModel, Field
from typing import List

class PatentClaim(BaseModel):
    claim_number: int
    is_independent: bool = False
    text: str = Field(..., description="The generated claim text. Must use formal patent legalese.")
    dependencies: List[int] = Field(default_factory=list, description="Claim numbers this claim depends on.")

class PatentEmbodiment(BaseModel):
    title: str
    description: str = Field(..., description="Detailed technical description enabling reproduction.")
    steps: List[str] = Field(..., description="Step-by-step implementation details.")

class PatentDisclosure(BaseModel):
    title: str
    background: str
    technical_problem: str
    technical_solution: str
    beneficial_effects: List[str]
    claims: List[PatentClaim]
    embodiments: List[PatentEmbodiment]
