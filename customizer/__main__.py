import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

import os
from pathlib import Path
from langchain_openai import AzureChatOpenAI

from resume_analysis import analyze_resume
from job_analysis import analyze_job_description
from review_resume import analyse_resume_structure


def get_chat_model() -> AzureChatOpenAI:
    """ Return chat model. Currently hardcoded to AzureChatOpenAI.
    """
    model = AzureChatOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
        openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION")
    )
    return model


def main():
    """ Resume customizer - customize markdown resume based on job offer.
    """
    chat_model = get_chat_model()

    # job_description = Path("jobs/rory.md").read_text()
    # job_analysis_results = analyze_job_description(job_description, chat_model)

    # print(f"--- JOB ANALYSIS ---")
    # print(job_analysis_results.model_dump_json(indent=4))
    # print()

    resume = Path("resume.md").read_text()
    # resume_analysis = analyze_resume(resume, chat_model)

    # print(f"--- RESUME ANALYSIS ---")
    # print(resume_analysis.model_dump_json(indent=4))
    # print()


    parsed, sections_review = analyse_resume_structure(resume, chat_model)

    print(sections_review)
    #print(parsed.model_dump_json(indent=4))


if __name__ == '__main__':
    main()
