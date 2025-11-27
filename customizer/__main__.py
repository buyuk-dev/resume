import logging
import datetime
import argparse
import json
import os
from pathlib import Path

from review import review_resume
from utils import transform_text
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def get_chat_model() -> AzureChatOpenAI:
    """ Return chat model. Currently hardcoded to AzureChatOpenAI.
    """
    model = AzureChatOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
        openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION")
    )
    return model

def guided_resolution(comment_text: str, resume_content: str, chat_model: AzureChatOpenAI) -> str:
    """
    Handle guided resolution flow for manual comments by dynamically generating 
    targeted follow-up questions and applying the fix automatically when sufficient
    context is gathered. If the agent cannot gather enough information, it will
    gracefully exit and continue to the next comment.

    Args:
        comment_text (str): The original manual comment requiring resolution.
        resume_content (str): The content of the resume being reviewed.
        chat_model (AzureChatOpenAI): The language model to assist with guided resolution.

    Returns:
        str: The resolved text based on user-provided clarifications, or None if unresolved.
    """
    print("Entering guided resolution mode for the following comment:")
    print(f"{comment_text}\n")

    context = []

    while True:
        # Combine the current context and generate the next follow-up question
        combined_context = "\n".join(context)
        question_prompt = (
            "You are assisting a user in resolving the following resume review comment:\n"
            f"{comment_text}\n"
            "Here is the current context provided by the user:\n"
            f"{combined_context}\n"
            "Here is the content of the resume:\n"
            f"{resume_content}\n"
            "Generate a specific, targeted, and closed-ended follow-up question to gather more context."
            " Ensure the question is actionable and can be answered swiftly. If sufficient context has been provided, respond with 'done'."
            " If it is not possible to resolve the comment due to insufficient information, respond with 'cannot resolve'."
        )

        system_message = SystemMessage(question_prompt)
        response = chat_model.invoke([system_message])
        follow_up_question = response.content.strip()

        if follow_up_question.lower() == "done":
            print("Agent: Sufficient context has been gathered. Applying the fix automatically...\n")
            break

        if follow_up_question.lower() == "cannot resolve":
            print("Agent: Unable to resolve this comment due to insufficient information. Skipping to the next comment.\n")
            return None

        # Ask the user the follow-up question
        user_answer = input(f"Agent: {follow_up_question}\nYou: ")
        context.append(f"Q: {follow_up_question}\nA: {user_answer.strip()}")

    # Combine the collected context into a single input for the agent
    final_context = "\n".join(context)

    # Use the transform_text function to generate the resolution
    resolution_prompt = (
        "Based on the following resume review comment and gathered context, apply the fix to the resume:\n"
        f"Comment: {comment_text}\n"
        f"Context:\n{final_context}\n"
        f"Resume Content:\n{resume_content}\n"
        "Return the updated resume content as a complete text."
    )

    resolution = transform_text(resume_content, resolution_prompt, chat_model)
    return resolution

def review_resume_interface(resume_content: str, style_guide: dict, chat_model: AzureChatOpenAI) -> dict:
    """Perform the review and return the results as a dictionary."""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    style_guide["current_date"] = current_date

    # Perform the review
    review = review_resume(resume_content, style_guide, chat_model, current_date=current_date)

    # Serialize the review output to JSON-like dictionary
    review_json = {
        "groups": [
            {
                "group_name": group.group_name,
                "comments": [
                    {"text": comment.text, "resolution_type": comment.resolution_type}
                    for comment in group.comments
                ]
            }
            for group in review.groups
        ]
    }
    return review_json

def resolve_comments_interface(
    resume_content: str, review_data: dict, chat_model: AzureChatOpenAI, user_input_callback
) -> str:
    """
    Resolve comments from review data and return the updated resume content.

    Args:
        resume_content (str): The content of the resume.
        review_data (dict): The review data containing comments to resolve.
        chat_model (AzureChatOpenAI): The chat model to assist with transformations.
        user_input_callback (function): A function to handle user input (replaces direct input calls).

    Returns:
        str: The updated resume content.
    """
    for group in review_data["groups"]:
        group_name = group["group_name"]
        logging.info(f"Resolving comments for group: {group_name}")

        for comment in group["comments"]:
            logging.info(f"Comment: {comment['text']} | Resolution Type: {comment['resolution_type']}")

            if comment["resolution_type"] == "automatic":
                # Apply the transformation automatically
                resume_content = transform_text(resume_content, comment["text"], chat_model)

            elif comment["resolution_type"] == "manual":
                # Ask the user what to do via the callback
                user_choice = user_input_callback(
                    comment["text"],
                    options=["Apply manually", "Attempt automatically", "Guided resolution"],
                )

                if user_choice == "Apply manually":
                    logging.info("Waiting for user to apply changes manually.")
                elif user_choice == "Attempt automatically":
                    additional_context = user_input_callback("Provide additional context (optional):", options=None)
                    transformation_text = comment["text"]
                    if additional_context:
                        transformation_text += f" Additional context: {additional_context}"
                    resume_content = transform_text(resume_content, transformation_text, chat_model)
                elif user_choice == "Guided resolution":
                    resolution = guided_resolution(comment["text"], resume_content, chat_model)
                    if resolution:
                        resume_content = resolution
                else:
                    logging.warning("Invalid choice. Skipping comment.")

    return resume_content

def main():
    """ Command-line interface for the resume customizer. """
    parser = argparse.ArgumentParser(description="Resume customizer tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Review subcommand
    review_parser = subparsers.add_parser("review", help="Generate review comments and store them in a JSON file.")
    review_parser.add_argument("resume", type=Path, help="Path to the resume file.")
    review_parser.add_argument("output", type=Path, help="Path to save the review JSON file.")

    # Resolve subcommand
    resolve_parser = subparsers.add_parser("resolve", help="Resolve review comments from a JSON file.")
    resolve_parser.add_argument("resume", type=Path, help="Path to the resume file.")
    resolve_parser.add_argument("review", type=Path, help="Path to the review JSON file.")

    # Customize subcommand
    customize_parser = subparsers.add_parser("customize", help="Placeholder for resume customization.")

    # Parse arguments
    args = parser.parse_args()
    chat_model = get_chat_model()

    if args.command == "review":
        resume_content = args.resume.read_text()
        style_guide = json.loads(Path("customizer/prompts/resume_style_guide.json").read_text())
        review_results = review_resume_interface(resume_content, style_guide, chat_model)
        args.output.write_text(json.dumps(review_results, indent=4))
        print(f"Review comments saved to {args.output}")

    elif args.command == "resolve":
        resume_content = args.resume.read_text()
        review_data = json.loads(args.review.read_text())

        def cli_user_input_callback(prompt, options):
            if options:
                print(prompt)
                for i, option in enumerate(options, 1):
                    print(f"{i}. {option}")
                choice = input("Enter your choice: ")
                return options[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(options) else ""
            else:
                return input(f"{prompt}: ")

        updated_resume = resolve_comments_interface(resume_content, review_data, chat_model, cli_user_input_callback)
        args.resume.write_text(updated_resume)
        print("Resume updated and saved.")

    elif args.command == "customize":
        print("Customize command is not yet implemented.")

if __name__ == "__main__":
    main()