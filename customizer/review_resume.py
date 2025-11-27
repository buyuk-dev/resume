import logging
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def transform_text(text: str, transform: str, model: BaseChatModel) -> str:
    logger.info("Applying transformation: %s", transform)
    prompt_path = Path("customizer/prompts/apply_text_modification.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [system_message, HumanMessage(text), HumanMessage(transform)]

    response = model.invoke(chat_history)
    return response.content


class ResumeSection(BaseModel):
    header: str = Field(description="Section name, header or title.")
    content: str = Field(
        description="Entire content of the section should be copied here."
    )
    has_subsections: bool = Field(
        description="Flag indicating whether this section has subsections, such as for work experience section which has subsection for every job, etc."
    )


class StructureAnalysisResults(BaseModel):
    sections: list[ResumeSection] = Field(
        description="List of analysis results for each section of the resume."
    )


class ReviewComments(BaseModel):
    comments: list[str] = Field(
        description="List of comments from the review. Each comment should be formulated so that it has a clear call to action."
    )


def parse_resume_structure(
    resume_content: str, model: BaseChatModel
) -> StructureAnalysisResults:
    prompt_path = Path("customizer/prompts/resume_sections_list.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [system_message, HumanMessage(resume_content)]

    model_with_schema = model.with_structured_output(StructureAnalysisResults)
    response = model_with_schema.invoke(chat_history)

    return response


def review_sections_list(
    sections: list[ResumeSection], model: BaseChatModel
) -> ReviewComments:
    logger.info("reviewing resume sections list")

    prompt_path = Path("customizer/prompts/review_sections_list.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [
        system_message,
        HumanMessage("\n".join([section.header for section in sections])),
    ]

    model_with_schema = model.with_structured_output(ReviewComments)
    response = model_with_schema.invoke(chat_history)

    logger.info("finished reviewing sections list")
    return response


def review_resume_structure(
    resume_content: str, model: BaseChatModel
) -> StructureAnalysisResults:
    logger.info("analysing resume structure...")

    sections_path = Path("cache/sections.json")
    if sections_path.exists() and sections_path.is_file():
        logger.info("loading sections from cached sections.json file")
        json_sections = sections_path.read_text()
        resume = StructureAnalysisResults.model_validate_json(json_sections)

    else:
        logger.info("parsing resume structure")
        resume = parse_resume_structure(resume_content, model)

        logger.info("caching resume structure in sections.json file")
        sections_path.write_text(resume.model_dump_json(indent=4))

    comments_path = Path("cache/comments.json")
    if comments_path.exists() and comments_path.is_file():
        logger.info("loading cached review comments from comments.json")
        comments = ReviewComments.model_validate_json(Path("comments.json").read_text())

    else:
        comments = review_sections_list(resume.sections, model)
        logger.info("caching comments from sections list review in comments.json file")
        Path("cache/comments.json").write_text(comments.model_dump_json(indent=4))

    logger.info("applying review comments...")
    for idx, comment in enumerate(comments.comments):

        if comment == "LGTM":
            logger.info("agent approved current resume structure")
            break

        else:
            resume_content = transform_text(resume_content, comment, model)
            Path(f"output/{idx}.md").write_text(resume_content)

        _ = input("press enter to continue...")

    logger.info("finished structural analysis")
    return resume, comments


def review_resume_section(
    resume_content: str, section: ResumeSection, model: BaseChatModel
) -> ReviewComments:
    logger.info("reviewing section %s", section.header)

    prompt_path = Path("customizer/prompts/review_resume_section.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [system_message, HumanMessage(section.content)]

    model_with_schema = model.with_structured_output(ReviewComments)
    response: ReviewComments = model_with_schema.invoke(chat_history)

    logger.info("applying review comments...")
    for idx, comment in enumerate(response.comments):

        if comment == "LGTM":
            logger.info("agent approved current resume structure")
            break

        else:
            resume_content = transform_text(resume_content, comment, model)
            Path(f"output/{idx}.md").write_text(resume_content)

        _ = input("press enter to continue...")
