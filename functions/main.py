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
    step = orchestrator.state["step"]
    num_questions = len(BASE_QUESTIONS)

    # handle the different stages of the dialog
    if step == 0 and not orchestrator.state["intro_done"]:
        orchestrator.state["intro_done"] = True
        orchestrator.state["step"] += 1
        return "\n".join(CREATE_INTRO)

    elif step == 1:
        orchestrator.state["resume"] = orchestrator.get_summary(user_message)
        orchestrator.state["step"] += 1
        return "Received resume"

    elif 2 <= step < num_questions * 2 + 1:
        if step % 2 == 0:  # Score the answer and provide follow-ups
            orchestrator.state, final_score = orchestrator.agent_scorer(user_message)
            if final_score <= 2:  # if the score is not satisfactory, ask a follow up
                return f"Follow-up question {orchestrator.state['question_index']}"
            else:
                orchestrator.state["step"] += 1
                return "Waiting..."

        else:  # Provide next question
            orchestrator.state = orchestrator.agent_question_maker()
            orchestrator.state["step"] += 1
            question = orchestrator.state["questions"][orchestrator.state["question_index"]]
            return f"Question #{orchestrator.state['question_index'] + 1}: {question}"

    elif step == num_questions * 2 + 1:  # At the end of the conversation
        summary_message = "\n".join([f"Q{q+1}: {question}\nA: {answer}\nScore: {score}" 
                                      for q, question, answer, score in zip(range(1, num_questions+1), 
                                                                           orchestrator.state["questions"], 
                                                                           orchestrator.state["answers"], 
                                                                           orchestrator.state["scores"])])
        # reset the state for next conversation
        orchestrator.reset_state()
        return f"Thank you for your time.\n\nSummary:\n{summary_message}"
