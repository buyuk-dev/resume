import json
import logging
from pathlib import Path
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReviewComment(BaseModel):
    """
    Represents a single review comment with resolution type.
    """

    text: str = Field(description="The content of the review comment.")
    resolution_type: str = Field(
        description="Indicates whether the comment can be resolved 'automatic' (clear action/change) or 'manual' (requires user input)."
    )


class ReviewGroup(BaseModel):
    """
    Represents a group of review comments for a specific guideline category.
    """

    group_name: str = Field(description="The name of the guideline group.")
    comments: List[ReviewComment] = Field(
        description="List of actionable review comments for this group."
    )


class Review(BaseModel):
    """
    A Pydantic model representing the structure of the review output.
    """

    groups: List[ReviewGroup] = Field(
        description="List of review groups with their associated comments."
    )


def review_resume(
    resume_content: str, style_guide: dict, model: BaseChatModel, current_date: str
) -> Review:
    """
    Reviews a resume by iterating over guideline groups in the style guide
    and dynamically generating comments for each group.

    Args:
        resume_content (str): The content of the resume to review.
        style_guide (dict): The style guide containing grouped guidelines.
        model (BaseChatModel): The language model to use for generating feedback.
        current_date (str): The current date to provide context for date-related checks.

    Returns:
        Review: A Pydantic Review object containing grouped review comments.
    """
    # Load the generic review prompt template
    prompt_template_path = Path("customizer/prompts/review_prompt_template.md")
    prompt_template = prompt_template_path.read_text()

    # Collect review comments for each guideline group
    review_groups: List[ReviewGroup] = []

    # Iterate over all guideline groups in the style guide
    for category, groups in style_guide.items():
        for group in groups:
            group_name = group["group_name"]
            guidelines = "\n".join(f"- {g}" for g in group["guidelines"])
            prompt = prompt_template.replace("{INSERT_GUIDELINES_HERE}", guidelines)
            prompt = prompt.replace("{CURRENT_DATE}", current_date)  # Add current date

            # Prepare chat messages
            system_message = SystemMessage(prompt)
            chat_history = [system_message, HumanMessage(resume_content)]

            # Call the model for the current guideline group
            logger.info(f"Reviewing guideline group: {group_name}")
            model_with_schema = model.with_structured_output(ReviewGroup)
            response: ReviewGroup = model_with_schema.invoke(chat_history)

            # Append the group to the results
            review_groups.append(response)

    return Review(groups=review_groups)