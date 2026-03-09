from pydantic import BaseModel, Field
from typing import List, Optional
from .common import Citation, Baseline, Dataset, TechnicalIndicator

class ResearchIdea(BaseModel):
    """
    Structured representation of a research idea.
    """
    title: str = Field(..., description="The title of the research paper.")
    scientific_problem: str = Field(..., description="The core scientific problem or gap being addressed. (解决的科学问题)")
    key_innovations: List[str] = Field(..., description="The primary novelties or key innovations. (关键的创新点)")
    methodology: str = Field(..., description="Proposed methodology and approach.")
    keywords: List[str] = Field(..., description="Key terms defining the research area.")
    baselines: List[Baseline] = Field(..., description="Existing methods to compare against.")
    related_work: str = Field(..., description="Summary of major related works and how this differs.")
    supporting_datasets: List[Dataset] = Field(..., description="Datasets required for experiments.")
    broader_impact: str = Field(..., description="Broader societal or community impact.")
    references: List[Citation] = Field(default_factory=list, description="List of structured citations.")
    abstract: Optional[str] = Field(None, description="The full abstract.")
    details: Optional[str] = Field(None, description="Detailed descriptive text (Markdown) of the idea.")
    technical_indicators: Optional[List[TechnicalIndicator]] = Field(None, description="Measurable keys (e.g. Accuracy > 95%).")
