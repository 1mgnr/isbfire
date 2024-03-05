from orchestrator import Orchestrator
from firebase_functions import https_fn
import firebase_admin
from firebase_admin import initialize_app, credentials, firestore
from firebase_functions.firestore_fn import on_document_created, Event, DocumentSnapshot
# from agent_functions import *
from send_reply import *
from config import *
import json

# Firebase Initialization
cred = credentials.Certificate("./serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()

orchestrator = Orchestrator(BASE_QUESTIONS)  # create the orchestrator instance

@on_document_created(document="messages/{messageId}")
def on_message_received(event: Event[DocumentSnapshot]) -> None:

    new_message_data = event.data.to_dict()

    doc_id = event.params["messageId"]

    # if the message is from the user, handle
    if new_message_data.get("role") == "human":
        user_message = new_message_data.get("message", "")

        response_message = handle_text_message(user_message)

        if response_message:
            send_reply(response_message)

    db.collection("messages").document(doc_id).update({"message_status": "message received"})


def send_reply(message):
    """Creates a new document with the reply message."""
    reply_document = {"message": message, "role": "bot", "timestamp": firestore.SERVER_TIMESTAMP}
    db.collection("messages").add(reply_document)

def handle_text_message(message):
    global orchestrator

    user_message = message
    num_questions = len(BASE_QUESTIONS)

    # Introduction
    if not orchestrator.state["intro_done"]:
        orchestrator.state["intro_done"] = True
        return "\n".join(CREATE_INTRO)

    # Resume reception
    elif orchestrator.state["step"] == 0:
        if len(user_message) < 50:  # check for adequate resume text
            return REQUEST_INADEQUATE_TEXT
        else:
            orchestrator.state["resume"] = orchestrator.get_summary(user_message)
            orchestrator.state["step"] += 1
            return "Received resume"

    # Answer reception
    elif orchestrator.state["step"] % 2 != 0:
        # answer reception from user
        orchestrator.state, final_score = orchestrator.agent_scorer(user_message)
        return f"Score #{orchestrator.state['question_index'] + 1}. Awaiting next question..."

    # Question generation
    elif orchestrator.state["step"] % 2 == 0 and orchestrator.state["step"] // 2 <= num_questions:
        orchestrator.agent_question_maker()  # Task the agent with generating the question
        question = orchestrator.state["questions"][orchestrator.state["question_index"]]
        orchestrator.state["step"] += 1
        return f"Question #{orchestrator.state['question_index'] + 1}: {question}"

    # All questions have been asked, reset the state for next conversation
    elif orchestrator.state["step"] // 2 > num_questions:
        orchestrator.reset_state()
        return "Thank you for your time. Please wait while we prepare your final results."

    return "Waiting for the candidate's response ..."