from pydantic import BaseModel, Field
from typing import List
from .common import Citation

class PaperSection(BaseModel):
    title: str
    content_tex: str
    figure_keys: List[str] = []

class ScientificPaper(BaseModel):
    title: str
    abstract: str
    keywords: List[str] = Field(default_factory=list, description="Keywords for the paper.")
    sections: List[PaperSection]
    citations: List[Citation]
    target_venue: str = "NeurIPS"
