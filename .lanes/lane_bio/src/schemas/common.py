from pydantic import BaseModel, Field
from typing import List, Optional

class Citation(BaseModel):
    """
    Structured academic citation.
    """
    key: str = Field(..., description="The citation key (e.g., Vaswani2017).")
    title: str = Field(..., description="Paper title.")
    authors: List[str] = Field(default_factory=list, description="List of author names.")
    year: int = Field(..., description="Publication year.")
    venue: Optional[str] = Field(None, description="Conference (e.g. NeurIPS) or Journal name.")
    url: Optional[str] = Field(None, description="Link to paper (ArXiv/DOI).")
    doi: Optional[str] = Field(None, description="Digital Object Identifier.")
    abstract: Optional[str] = Field(None, description="Paper abstract.")

    references: List['Citation'] = Field(default_factory=list, description="List of structured citations.")

class Dataset(BaseModel):
    name: str = Field(..., description="Name of the dataset.")
    description: Optional[str] = Field(None, description="Brief description or usage.")
    url: Optional[str] = Field(None, description="URL to dataset.")

class Baseline(BaseModel):
    name: str = Field(..., description="Name of the baseline method.")
    description: Optional[str] = Field(None, description="Why this baseline is relevant.")
    citation_key: Optional[str] = Field(None, description="Key of the citation in references.")

class TechnicalIndicator(BaseModel):
    name: str = Field(..., description="Metric name (e.g. Accuracy).")
    target_value: str = Field(..., description="Target value (e.g. > 95% or SOTA + 2%).")
    description: Optional[str] = Field(None, description="rationale for this metric.")
