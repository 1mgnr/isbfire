# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
import firebase_admin
from firebase_admin import initialize_app, credentials
from config import *
from agent_functions import *
from send_reply import *
import json

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)


@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    handle_text_message("hello there")
    return https_fn.Response("Hello world!")


from firebase_functions.firestore_fn import (
    on_document_created,
    Event,
    DocumentSnapshot,
)
from firebase_admin import firestore
db = firestore.client()


@on_document_created(document="messages/{messageId}")
def on_message_received(event: Event[DocumentSnapshot]) -> None:
    # Initialize Firestore DB if not already done (assuming Firebase Admin is initialized)

    # Get a dictionary representing the document, e.g. {'text': 'Hello', 'timestamp': ...}
    new_message_data = event.data.to_dict()

    # Assuming you want to log the message or do additional processing
    print(f"New message received: {new_message_data}")

    # The document path is provided by the event; it includes the collection and document ID
    doc_id = event.params[
        "messageId"
    ]  # Assuming 'event.context.resource' gives the full path
    # Parse the document ID from the resource path
    # This approach depends on the actual structure of 'event.context.resource'
    print(f"New message received: {new_message_data}")

    # Check if the message is from the user and needs processing
    if new_message_data.get("role") == "human":
        user_message = new_message_data.get("message", "")

        # Process the message using an orchestrator
        # and collect a response (simulate this with a function call)
        # The function `handle_text_message` is expected to return
        # the response from the orchestrator for simplicity in this example.
        response_message = handle_text_message(user_message)

        # After receiving the response, create a new document using 'send_reply'
        # Depending on the return type of `handle_text_message`, adjust as needed
        if response_message:
            send_reply(response_message)
    # Now, update the document to set 'message_status' to 'message received'

    db.collection("messages").document(doc_id).update(
        {"message_status": "message received"}
    )

    print(f"Message status updated for: {doc_id}")


def send_reply(message):
    db = firestore.client()

    """Creates a new document with the reply message."""
    reply_document = {
        "message": message,
        "role": "bot",  # Assuming the response role to be 'bot' for simplicity
        "timestamp": firestore.SERVER_TIMESTAMP,
    }
    db.collection("messages").add(reply_document)
    print("Reply message sent and saved to Firestore.")


conversation_state = {
    "step": 0,
    "question_index": 0,  # new addition
    "intro_done": False,
    "resume": "",
    "questions": ["" for _ in range(len(BASE_QUESTIONS))],
    "answers": ["" for _ in range(len(BASE_QUESTIONS))],
    "scores": [""] * len(BASE_QUESTIONS),
}


def handle_text_message(message):
    global conversation_state
    user_message = message
    num_questions = len(BASE_QUESTIONS)
    print("hello world 001")

    if not conversation_state["intro_done"]:
        for intro in CREATE_INTRO:
            print(intro)
            send_reply(intro)
        conversation_state["intro_done"] = True

    elif conversation_state["step"] == 0:
        if len(user_message) < 50:  # check for adequate resume text
            send_reply(REQUEST_INADEQUATE_TEXT)
        else:
            conversation_state["resume"] = get_summary(user_message)
            print(
                f"\nBEGIN NEW LOOP\nReceived candidate's resume:\n{conversation_state['resume']}\n"
            )
            send_reply(RESUME_RECEIVED)  # Acknowledge receipt of resume

            conversation_state["step"] += 1  # Increase the step

            # Generate the first question in same iteration
            conversation_state = question_retrieval(conversation_state)
            # Send the first question to the candidate on telegram
            send_reply(
                conversation_state["questions"][conversation_state["question_index"]]
            )

    elif 1 <= conversation_state["step"] < num_questions * 2 + 1:
        if conversation_state["step"] % 2 == 0:  # Receive Answer, Score it
            conversation_state, doc_to_save = receive_answer_and_score_it(
                conversation_state, user_message
            )
            print(json.loads(doc_to_save))
            # Save doc_to_save to Firestore
            try:
                db.collection(SCORES_COLLECTION).add(json.loads(doc_to_save))  # Choose your collection name
                print("Document saved successfully.")
            except Exception as e:
                print(f"Failed to save document: {e}")
            send_reply(WAIT_MSG)

        elif conversation_state["step"] % 2 == 1:  # Generate Next Question
            conversation_state = question_retrieval(conversation_state)
            send_reply(
                conversation_state["questions"][conversation_state["question_index"]]
            )  # Send the question to candidate on telegram

    elif conversation_state["step"] == num_questions * 2 + 1:
        thankyouPrompt_system_message = "Craft a polite and professional thank you or follow-up message that consolidates the conversation and reciprocates the candidate's responses. Within 20 words"
        thank_you_message = orchestrator.assistant.converse(
            thankyouPrompt_system_message, "Generate a thank you message"
        )

        summary_message = "\n".join(
            [
                f'Question {i+1}: {conversation_state["questions"][i]}\nAnswer: {conversation_state["answers"][i]}\nScore: {conversation_state["scores"][i]}'
                for i in range(len(BASE_QUESTIONS))
            ]
        )

        print(
            f"\nAssessment Summary:\n{summary_message}\n\nThank You Message:\n{thank_you_message}\n========================== END ==========================\n"
        )

        send_reply(
            thank_you_message
        )  # Send thank you message to the candidate on telegram

        conversation_state = reset_conversation_state()  # Reset conversation state
