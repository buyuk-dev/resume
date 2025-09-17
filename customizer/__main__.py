import logging
import datetime
import argparse
import json
import os
from pathlib import Path

from review import review_resume
from utils import transform_text
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

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

def review_command(resume_path: Path, output_path: Path, chat_model: AzureChatOpenAI):
    """ Generate review comments and store them in a JSON file. """
    # Load the style guide
    style_guide: dict = json.loads(Path("customizer/prompts/resume_style_guide.json").read_text())

    # Load the resume content
    resume = resume_path.read_text()

    # Inject current date for context
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Perform the review
    review = review_resume(resume, style_guide, chat_model, current_date=current_date)

    # Serialize the review output to JSON
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

    # Save the review to a JSON file
    output_path.write_text(json.dumps(review_json, indent=4))
    print(f"Review comments saved to {output_path}")

def resolve_command(resume_path: Path, review_path: Path, chat_model: AzureChatOpenAI):
    """ Load review comments from JSON file and resolve them. """
    # Load the resume content
    resume = resume_path.read_text()

    # Load the review comments
    review_data = json.loads(review_path.read_text())

    for group in review_data["groups"]:
        group_name = group["group_name"]
        print(f"Resolving comments for group: {group_name}")

        for comment in group["comments"]:
            print(f"Comment: {comment['text']}")
            print(f"Resolution Type: {comment['resolution_type']}")

            if comment["resolution_type"] == "automatic":
                # Apply the transformation automatically
                resume = transform_text(resume, comment["text"], chat_model)
                resume_path.write_text(resume)
                print("Automated transformation applied and saved.")

            elif comment["resolution_type"] == "manual":
                # Ask the user what to do
                user_choice = input("This comment requires manual intervention. Would you like to: \n"
                                    "1. Apply the change manually \n"
                                    "2. Let the agent attempt to apply it automatically \n"
                                    "3. Enter guided resolution mode \n"
                                    "Enter your choice (1/2/3): ")

                if user_choice == "1":
                    print("Please make the change manually, then press any key to continue.")
                    input()  # Wait for user input
                elif user_choice == "2":
                    additional_comment = input("Enter additional context or instructions for the agent (or press Enter to skip): ")
                    transformation_text = comment["text"]
                    if additional_comment:
                        transformation_text += f" Additional context: {additional_comment}"
                    resume = transform_text(resume, transformation_text, chat_model)
                    resume_path.write_text(resume)
                    print("Agent attempted transformation and saved.")
                elif user_choice == "3":
                    resolution = guided_resolution(comment["text"], resume, chat_model)
                    if resolution:
                        resume = resolution
                        resume_path.write_text(resume)
                        print("Guided resolution applied and saved.")
                else:
                    print("Invalid choice. Skipping this comment.")

    print("All changes applied. Review process complete.")

def customize_command():
    """ Placeholder for future implementation of resume customization. """
    print("Customize command is not yet implemented.")

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
        review_command(args.resume, args.output, chat_model)
    elif args.command == "resolve":
        resolve_command(args.resume, args.review, chat_model)
    elif args.command == "customize":
        customize_command()

if __name__ == "__main__":
    main()