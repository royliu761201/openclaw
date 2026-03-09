from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from .common import Citation, TechnicalIndicator

class BudgetItem(BaseModel):
    category: str = Field(..., description="Equipment, Material, Travel, Labor, Other")
    description: str
    amount_rmb: float
    justification: str
    funding_source: Literal["Government Grant", "Self-raised"] = Field(default="Government Grant", description="Source of funds.")

class GrantMilestone(BaseModel):
    year: int = Field(..., description="Calendar year (e.g. 2026).")
    quarter: Literal["Q1", "Q2", "Q3", "Q4"] = Field(..., description="Fiscal/Calendar Quarter.")
    deliverables: List[str] = Field(..., description="Tangible outputs (reports, prototypes).")
    completion_indicators: List[str] = Field(default_factory=list, description="Technical indicators achieved (e.g. 'Latency < 10ms').")

class PastGrant(BaseModel):
    grant_number: str = Field(..., description="Grant ID (基金编号).")
    grant_type: Literal["National", "Provincial", "Corporate", "Other"] = Field(..., description="Level (National/Provincial).")
    amount_rmb: float = Field(..., description="Grant amount in RMB.")
    start_date: str = Field(..., description="Start date (YYYY-MM).")
    end_date: str = Field(..., description="End date (YYYY-MM).")
    title: str = Field(..., description="Grant title.")

class GrantAward(BaseModel):
    name: str = Field(..., description="Award Name (e.g. State Natural Science Award).")
    level: Literal["National", "Provincial", "Association", "Other"] = Field(..., description="Award Level (国家级/省部级).")
    year: int = Field(..., description="Year received.")

class GrantAchievements(BaseModel):
    past_grants: List[PastGrant] = Field(default_factory=list, description="Previous grants held by leader.")
    papers: List[Citation] = Field(default_factory=list, description="Representative publications.")
    patents: List[Citation] = Field(default_factory=list, description="Authorized patents (use Citation format).")
    standards: List[Citation] = Field(default_factory=list, description="Published standards (use Citation format).")
    awards: List[GrantAward] = Field(default_factory=list, description="Awards received.")
    talent_titles: List[str] = Field(default_factory=list, description="Talent titles (e.g. Distinguished Young Scholar).")

class GrantPlatform(BaseModel):
    platform_name: str = Field(..., description="Name of the supporting platform/lab (依托平台名称).")
    platform_leader: str = Field(..., description="Leader/Director of the platform.")
    platform_talents: List[str] = Field(default_factory=list, description="Key talents in the platform.")
    platform_awards: List[GrantAward] = Field(default_factory=list)
    major_equipment: List[str] = Field(default_factory=list, description="Key equipment available.")
    conditions: str = Field(..., description="Experimental and data conditions.")

class GrantFoundation(BaseModel):
    completed_work: str = Field(..., description="Preliminary work completed.")
    leader_achievements: GrantAchievements
    team_intro: str = Field(..., description="Introduction of core team members.")
    platform: GrantPlatform
    collaborating_units: List[str] = Field(default_factory=list, description="Collaborating units/teams.")

class GrantTask(BaseModel):
    task_name: str = Field(..., description="Name of the sub-task (课题名称).")
    task_leader: str = Field(..., description="Leader of this sub-task.")
    team_members: List[str] = Field(..., description="Team members for this specific task.")
    budget_allocated: float = Field(..., description="Budget allocated to this task.")
    research_content: str = Field(..., description="Specific content for this task.")
    technical_indicators: List[TechnicalIndicator] = Field(default_factory=list, description="KPIs for this sub-task.")
    foundation: GrantFoundation = Field(..., description="Foundation/Basis for this task.")

class GrantApplication(BaseModel):
    """
    Structured Grant Application (NSFC-style).
    Reflects the strict sectioning required by funding agencies.
    """
    project_title: str
    project_leader: str = Field(..., description="Overall Project Leader (项目负责人).")
    application_type: Literal["Regular", "Program"] = Field(default="Regular", description="Regular (Single Task) or Program (Multi-Task).")
    duration_months: int
    budget_request_rmb: float = Field(..., description="Amount requested from government.")
    budget_self_raised_rmb: float = Field(0.0, description="Amount matched by institution/self.")
    
    # Part 1: Background
    strategic_necessity: str = Field(..., description="Why this is critical for national/strategic needs.")
    scientific_gap: str = Field(..., description="The specific gap in current knowledge.")
    
    # Part 2: Content & Targets
    scientific_content: str = Field(..., description="Main research content.")
    key_question: str = Field(..., description="Core scientific question.")
    technical_indicators: List[TechnicalIndicator] = Field(..., description="Specific, measurable KPIs (e.g. Latency < 10ms).")
    
    # Part 2: Innovation
    innovation_points: List[str] = Field(..., description="Key innovations (usually 3 distinct points).")

    # Part 3: Methodology
    methodology: str
    feasibility_analysis: str
    
    # Part 4: Foundation
    foundation: GrantFoundation = Field(..., description="Basis of the project (or main task).")
    
    # Part 5: Budget & Timeline
    budget_plan: List[BudgetItem]
    timeline: List[GrantMilestone]

    # Part 6: Sub-tasks (for Programs)
    sub_tasks: List[GrantTask] = Field(default_factory=list, description="Breakdown into sub-tasks (课题) if Program. If Regular, contains 1 main task.")
