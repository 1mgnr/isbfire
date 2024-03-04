from firebase_functions import https_fn
import firebase_admin
from firebase_admin import initialize_app, credentials, firestore
from firebase_functions.firestore_fn import on_document_created, Event, DocumentSnapshot
from agent_functions import *
from send_reply import *
from config import *
import json

# Firebase Initialization
cred = credentials.Certificate("./serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()

# @https_fn.on_request()
# def on_request_example(req: https_fn.Request) -> https_fn.Response:
#     handle_text_message("hello there")
#     return https_fn.Response("Hello world!")


@on_document_created(document="messages/{messageId}")
def on_message_received(event: Event[DocumentSnapshot]) -> None:

    new_message_data = event.data.to_dict()
    print(f"New message received: {new_message_data}")

    doc_id = event.params["messageId"]

    print(f"New message received: {new_message_data}")

    # Check if the message is from the user and needs processing
    if new_message_data.get("role") == "human":
        user_message = new_message_data.get("message", "")

        response_message = handle_text_message(user_message)

        if response_message:
            send_reply(response_message)

    db.collection("messages").document(doc_id).update(
        {"message_status": "message received"}
    )

    print(f"Message status updated for: {doc_id}")


def send_reply(message):

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
            conversation_state = agent_1_question_maker(conversation_state)
            # Send the first question to the candidate on telegram
            send_reply(
                conversation_state["questions"][conversation_state["question_index"]]
            )

    elif 1 <= conversation_state["step"] < num_questions * 2 + 1:
        if conversation_state["step"] % 2 == 0:  # Receive Answer, Score it
            conversation_state, doc_to_save, is_satisfactory = agent_3_scorer(
                conversation_state, user_message
            )
            print(json.loads(doc_to_save))

            if not is_satisfactory:
                followup_question = agent_3_scorer(conversation_state, user_message)
                send_reply(followup_question)
            # Save doc_to_save to Firestore
            try:
                db.collection(SCORES_COLLECTION).add(json.loads(doc_to_save))  # Choose your collection name
                print("Document saved successfully.")
            except Exception as e:
                print(f"Failed to save document: {e}")
            send_reply(WAIT_MSG)

        elif conversation_state["step"] % 2 == 1:  # Generate Next Question
            conversation_state = agent_1_question_maker(conversation_state)
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
