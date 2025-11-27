from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class JobDescriptionAnalysisResults(BaseModel):
    """Always use this tool to structure your response to the user."""

    responsibilities: list[str] = Field(
        description="list of primary duties and responsibilities associated with the position."
    )
    qualifications: list[str] = Field(
        description="list of any specific educational or certification requirements, as well as years of experience needed."
    )
    company_values: list[str] = Field(
        description="list of any hints about the company's culture, values, or preferred work style."
    )
    desired_outcomes: list[str] = Field(
        description="list of goals or outcomes expected from the role."
    )
    tech_stack: list[str] = Field(
        description="list of languages, frameworks and other tools used in the project associated with this position."
    )
    keywords: list[str] = Field(
        description="list of specific terms that are frequently mentioned, such as required skills, technologies, and methodologies."
    )


def analyze_job_description(
    job_description: str, model: BaseChatModel
) -> JobDescriptionAnalysisResults:
    """Analyze job description and return JobDescriptionAnalysisResults instance."""
    prompt_path = Path("customizer/prompts/analysis.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [system_message, HumanMessage(job_description)]

    model_with_schema = model.with_structured_output(JobDescriptionAnalysisResults)
    response = model_with_schema.invoke(chat_history)

    return response
