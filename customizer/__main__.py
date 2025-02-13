import os
from pathlib import Path
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field


def get_chat_model() -> AzureChatOpenAI:
    """ Return chat model. Currently hardcoded to AzureChatOpenAI.
    """
    model = AzureChatOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
        openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION")
    )
    return model


class AnalysisResults(BaseModel):
    """ Always use this tool to structure your response to the user.
    """
    responsibilities: list[str] = Field(description="list of primary duties and responsibilities associated with the position.")
    qualifications: list[str] = Field(description="list of any specific educational or certification requirements, as well as years of experience needed.")
    company_values: list[str] = Field(description="list of any hints about the company's culture, values, or preferred work style.")
    desired_outcomes: list[str] = Field(description="list of goals or outcomes expected from the role.")
    tech_stack: list[str] = Field(description="list of languages, frameworks and other tools used in the project associated with this position.")
    keywords: list[str] = Field(description="list of specific terms that are frequently mentioned, such as required skills, technologies, and methodologies.")



def load_system_message(prompt_file_path: str) -> SystemMessage:
    """ Load system prompt from file and return SystemMessage instance.
    """
    prompt_path = Path(prompt_file_path)
    return SystemMessage(prompt_path.read_text())


def analyze_job_description(job_description: str, model: BaseChatModel) -> AnalysisResults:
    """ Analyze job description and return AnalysisResults instance.
    """
    system_message = load_system_message("customizer/prompts/analysis.md")
    chat_history = [
        system_message,
        HumanMessage(job_description)
    ]

    model_with_schema = model.bind_tools([AnalysisResults])
    response = model_with_schema.invoke(chat_history)

    return AnalysisResults.model_validate(response.tool_calls[0]["args"])


def main():
    """ Resume customizer - customize markdown resume based on job offer.
    """
    chat_model = get_chat_model()

    job_description = Path("jobs/rory.md").read_text()
    analysis_results = analyze_job_description(job_description, chat_model)

    print(analysis_results.model_dump_json(indent=4))


if __name__ == '__main__':
    main()
