import os
import logging
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def load_resume(path: str) -> str:
    resume_path = Path(path)
    if not resume_path.exists() and resume_path.is_file():
        raise FileNotFoundError(path)
    return resume_path.read_text()


class ResumeSection(BaseModel):
    header: str = Field(description="Section name, header or title.")
    content: str = Field(description="Entire content of the section should be copied here.")
    has_subsections: bool = Field(description="Flag indicating whether this section has subsections, such as for work experience section which has subsection for every job, etc.")


class StructureAnalysisResults(BaseModel):
    sections: list[ResumeSection] = Field(description="List of analysis results for each section of the resume.")


def parse_resume_structure(resume_content: str, model: BaseChatModel) -> StructureAnalysisResults:
    prompt_path = Path("customizer/prompts/resume_sections_list.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [
        system_message,
        HumanMessage(resume_content)
    ]

    model_with_schema = model.with_structured_output(StructureAnalysisResults)
    response = model_with_schema.invoke(chat_history)

    return response


class ReviewComments(BaseModel):
    comments: list[str] = Field(description="List of comments from the review. Each comment should be formulated so that it has a clear call to action.")


def review_sections_list(sections: list[ResumeSection], model: BaseChatModel) -> ReviewComments:
    prompt_path = Path("customizer/prompts/review_sections_list.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [
        system_message,
        HumanMessage(
            "\n".join([
                section.header for section in sections
            ])
        )
    ]

    model_with_schema = model.with_structured_output(ReviewComments)
    response = model_with_schema.invoke(chat_history)

    return response


def transform_text(text: str, transform: str, model: BaseChatModel) -> str:
    logger.info("Applying transformation: %s", transform)
    prompt_path = Path("customizer/prompts/apply_text_modification.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [
        system_message,
        HumanMessage(text),
        HumanMessage(transform)
    ]

    response = model.invoke(chat_history)
    return response.content


def analyse_resume_structure(resume_content: str, model: BaseChatModel) -> StructureAnalysisResults:
    #resume = parse_resume_structure(resume_content, model)
    #Path("sections.json").write_text(resume.model_dump_json(indent=4))

    json_sections = Path("sections.json").read_text()
    resume = StructureAnalysisResults.model_validate_json(json_sections)

    #comments = review_sections_list(resume.sections, model)
    #Path("comments.json").write_text(comments.model_dump_json(indent=4))

    comments = ReviewComments.model_validate_json(Path("comments.json").read_text())
    for idx, comment in enumerate(comments.comments):
        resume_content = transform_text(resume_content, comment, model)
        Path(f"transformed/{idx}.md").write_text(resume_content)
        _ = input("press enter to continue...")

    return resume, comments
