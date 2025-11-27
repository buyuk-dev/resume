import logging
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


def transform_text(text: str, transform: str, model: BaseChatModel) -> str:
    logger.info("Applying transformation: %s", transform)
    prompt_path = Path("customizer/prompts/apply_text_modification.md")
    system_message = SystemMessage(prompt_path.read_text())

    chat_history = [system_message, HumanMessage(text), HumanMessage(transform)]

    response = model.invoke(chat_history)
    return response.content
