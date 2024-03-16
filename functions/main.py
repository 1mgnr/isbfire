# from firebase_functions import https_fn
# import firebase_admin
from firebase_admin import initialize_app, credentials, firestore
from firebase_functions.firestore_fn import on_document_created, Event, DocumentSnapshot
from agents import *
from config import *
import json
import uuid

# Firebase Initialization
cred = credentials.Certificate("./serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()


conversation_state = {
        "interview_id": "",  
        "step": 0,
        "intro_done": False,
        "resume": "",
        "interview": [],  # Stores QA pairs with score
        "current_q_index": 0,
}


# #####################
@on_document_created(document="messages/{messageId}")
def on_message_received(event: Event[DocumentSnapshot]) -> None:
    """Handle new messages as Firestore Document creates events."""
    print("NEW DOC CREATED")
    new_message_data = event.data.to_dict()

    if new_message_data.get("role") == "human":
        handle_text_message(new_message_data.get("message", ""))

    doc_id = event.params["messageId"]
    db.collection("messages").document(doc_id).update({"message_status": "message received"})


# #####################
def handle_text_message(message):
    """Process received text messages during the interview."""
    global conversation_state
    print("HANDLE MESSAGE CALLED")

    if not conversation_state["intro_done"]:
        greeting_and_resume_request()
    elif conversation_state["step"] == 0:
        process_resume_submission(message)
    else:
        process_interview_step(message)


# #####################
def process_interview_step(message):
    """
    Handles processing the received message in the context of the interview.
    """
    global conversation_state
    if conversation_state["step"] % 2 == 0:  # Even steps are for processing answers
        current_qa_index = len(conversation_state["interview"]) - 1
        current_qa = conversation_state["interview"][current_qa_index]
        current_qa["answer"] = message
        
        score_dict, data_to_save, is_satisfactory = agent_3_scorer(
            message, 
            current_qa["question"], 
            current_qa_index
        )

        db.collection("scores").document().set(data_to_save)

        print(">>>>> SCORE INFO >>>>>", score_dict)
        
        current_qa["score"] = score_dict["score"]
        if not is_satisfactory:
            # Handle the follow-up scenario // add a skip question
            followup_question = agent_2_followup_question_maker(conversation_state["resume"],current_qa_index,current_qa["question"],message)
            send_reply("I would like to know more, let me rephrase!")
            send_reply(followup_question)
        else:
            conversation_state["step"] += 1  # Proceed to next question or wrap-up
            send_reply("I see")
        
        # Save score information and satisfaction determination
        current_qa["score_info"] = score_dict
        current_qa["is_satisfactory"] = is_satisfactory

    
    elif conversation_state["step"] % 2 == 1:  # Odd steps are for asking next question
        print(">>>>>> WE'RE IN ELIF >>>>>", conversation_state["step"])
        
        if conversation_state["current_q_index"] < len(BASE_QUESTIONS) - 1:
            conversation_state["current_q_index"] += 1
            prompt_next_question()
            conversation_state["step"] += 1

        else:
            complete_interview()




# ######################################################################## #

def greeting_and_resume_request():
    """Send a greeting and request for the resume."""

    send_reply("Hello! Welcome to your interview. Please paste your resume text here.")
    conversation_state["intro_done"] = True



# #####################
# @on_document_created(document="trigger/{triggerId}")
# def on_message_received(event: Event[DocumentSnapshot]) -> None:
#     """Handle new messages as Firestore Document creates events."""
#     conversation_state["interview_id"] = str(uuid.uuid4())

#     db.collection("thread").document(conversation_state["interview_id"]).set({
#         "timestamp": firestore.SERVER_TIMESTAMP,
#         "thread_id": conversation_state["interview_id"]
#     })



def process_resume_submission(message):
    """Handle resume submission and verify its adequacy."""
    global conversation_state

    if len(message) < 50:
        send_reply(REQUEST_INADEQUATE_TEXT)
    else:
        conversation_state["resume"] = get_summary(message)  # Assuming get_summary is implemented
        send_reply(RESUME_RECEIVED)
        conversation_state["step"] = 1


def prompt_next_question():
    print("QUE INDEX",conversation_state["current_q_index"])
    next_question = agent_1_question_maker(conversation_state["resume"],conversation_state["current_q_index"])
    if next_question:
        conversation_state["interview"].append({"question": next_question, "answer": "", "score": None})
        send_reply(next_question)
    else:
        # No more questions, conclude interview
        complete_interview()




def send_reply(message):

    """Creates a new document with the reply message."""
    reply_document = {
        "message": message,
        "role": "bot",  # Assuming the response role to be 'bot' for simplicity
        "timestamp": firestore.SERVER_TIMESTAMP,
        "interview_id": conversation_state["interview_id"],  # Include interview_id

    }
    db.collection("messages").add(reply_document)
    print("Reply message sent and saved to Firestore.")


def complete_interview():
    global conversation_state
    
    # SAVE CONVERSATION WITH SCORES TO THE DATABASE
    interview_data_with_id = {**conversation_state, "interview_id": conversation_state["interview_id"]}

    db.collection("logs").document().set(interview_data_with_id)

    summary_message = "Interview Summary:\n" + "\n".join(
        f'Q: {qa["question"]} A: {qa["answer"]} Score: {qa.get("score", "N/A")}' for qa in conversation_state["interview"]
    )
    print(summary_message)
    send_reply("Thank you for participating in the interview.")
    conversation_state = reset_conversation_state()  # Reset for possibly the next interview

