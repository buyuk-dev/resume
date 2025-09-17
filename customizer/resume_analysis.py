from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Description of a project described in the resume."""

    name: str = Field(description="Project name (or a headline)")
    description: str = Field(description="Brief project description.")
    skills: list[str] = Field(description="Skilles used in that project.")
    achievements: list[str] = Field(
        description="List of key achievements in this project if available."
    )


class AdditionalSectionInfo(BaseModel):
    header: str = Field(description="Section header")
    content: str = Field(description="Section content")


class ContactInfo(BaseModel):
    method: str = Field(
        description="Contact method (eg. email, address, phone, linkedin, etc...)."
    )
    info: str = Field(description="Contact info for this method.")


class ResumeDataExtraction(BaseModel):
    """Always use this tool to structure your response to the user."""

    contact_info: list[ContactInfo] = Field(
        description="List of contact information extracted from the resume."
    )
    professional_summary: str = Field(
        description="A brief summary or objective statement from the resume."
    )
    experience: list[str] = Field(
        description="List of work experiences represented like job title, company, duration, and responsibilities."
    )
    skills: list[str] = Field(
        description="List of technical and soft skills mentioned in the resume."
    )
    education: list[str] = Field(
        description="List of educational qualifications including degree, institution, and graduation date represented as json dicts."
    )
    certifications: list[str] = Field(
        description="List of certifications and trainings completed by the candidate."
    )
    projects: list[ProjectInfo] = Field(
        description="List of significant projects or accomplishments with brief descriptions."
    )
    additional_sections: list[AdditionalSectionInfo] = Field(
        description="List of additional sections like languages, volunteer work, hobbies."
    )


def analyze_resume(resume: str, model: BaseChatModel) -> ResumeDataExtraction:
    """Analyze resume and return ResumeDataExtraction instance."""
    prompt_path = Path("customizer/prompts/resume_analysis.md")
    system_message = SystemMessage(prompt_path.read_text(prompt_path))

    chat_history = [system_message, HumanMessage(resume)]

    model_with_schema = model.with_structured_output(ResumeDataExtraction)
    response = model_with_schema.invoke(chat_history)

    return response
