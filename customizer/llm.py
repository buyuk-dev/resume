"""
Module for interacting with the language model (LLM) using OpenAI's API.
Provides classes for handling errors and sending messages to the LLM.
"""

import logging
import os
from typing import List, Optional

import openai
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai.chat_models import AzureChatOpenAI, ChatOpenAI

logger = logging.getLogger(__name__)


class LlmError(Exception):
    """
    Custom exception for errors related to the language model (LLM).
    """

    pass


class ChatModel:
    """
    Class for interacting with the language model (LLM) using OpenAI's API.

    Attributes:
        client (openai.Client): The OpenAI client for interacting with the API.
        model (str): The model to use for generating responses.
        system_message (str): The system message for setting the context of the conversation.
        temperature (float): The temperature for controlling the randomness of the responses.
        max_tokens (int or None): The maximum number of tokens for the response.
    """

    def __init__(self, system_message: str, model: str = "gpt-4o-mini"):
        """
        Initializes the ChatModel with the specified system message and model.

        Args:
            system_message (str): The system message for setting the context of the conversation.
            model (str): The model to use for generating responses. Defaults to "gpt-4o-mini".
        """
        self.client = openai.Client()
        self.model = model
        self.system_message = system_message
        self.temperature = 0.2
        self.max_tokens = None

    def send(self, message) -> str:
        """
        Sends a message to the language model (LLM) and returns the response.

        Args:
            message (str): The message to send to the LLM.

        Returns:
            str: The response from the LLM.

        Raises:
            LlmError: If an error occurs while sending the message to the LLM.
        """
        print(f"sending message to llm: {message}")
        try:
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": message},
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=None,
                seed=None,
                # response_format={"type": "json_object"}
            )

            return response.choices[0].message.content

        except Exception as error:
            raise LlmError("sending message to ChatModel failed") from error


def load_model(provider: Optional[str] = None, model: Optional[str] = None):
    """
    Returns the model based on the provider.
    """
    MODELS = {
        "openai": {
            "models": ["o3-mini", "gpt-4o-mini", "gpt-4o"],
            "class": ChatOpenAI,
        },
        "azure": {
            "models": ["gpt-4o", "gpt-4o-mini"],
            "class": AzureChatOpenAI,
        },
        "ollama": {
            "models": ["llama3.1"],
            "class": ChatOllama,
        },
        "groq": {
            "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant"],
            "class": ChatGroq,
        },
    }

    if not provider:
        provider = "azure"

    if not model:
        model = MODELS.get(provider).get("models")[0]

    class_ = MODELS.get(provider).get("class")

    logger.info("Provider: %s, Model: %s, Class_: %s", provider, model, class_)
    return class_(model=model)
