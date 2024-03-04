
from config import *
from orchestrator import Orchestrator, OpenAIAssistant  # import necessary classes
import prompts as prompt

assistant = OpenAIAssistant()  # instantiate the assistant
orchestrator = Orchestrator(assistant)  # instantiate the orchestrator


def question_retrieval(state):
    # Get the base question first
    base_question = BASE_QUESTIONS[state['question_index']]
    
    # The rest of this function stays essentially the same
    state["questions"][state["question_index"]] = orchestrator.assistant.converse(prompt.QUESTION_BUILDER(state, base_question), f"Use the resume: {state['resume']}, previous Question: {state['questions']} generate a relevant question")
    
    # Increase the step
    state["step"] += 1
    
    # Return updated state
    return state


def receive_answer_and_score_it(state, answer):

    base_question = BASE_QUESTIONS[state["question_index"]]

    state["answers"][state["question_index"]] = answer  # Save the candidate's answer
    
    print(f"\nReceived Candidate's Answer {state['question_index'] + 1}:\n{state['answers']}{state['question_index']}\n")  # Log answer to console
        
    score = orchestrator.assistant.converse(
        prompt.SCORER(base_question), f"Given the scoring guidelines mentioned above, please assess the following answer: {state['answers'][state['question_index']]}, with respect to the question: {state['questions'][state['question_index']]} and relevance to {base_question}. Give response in a json object with score, the description, base question, question and answer")
    
    print(f"\nAssessed Score for Question {state['question_index'] + 1}:\n{score}\n")  # Log score to console

    # Prepare document to save
    doc_to_save = score
    
    state["scores"][state["question_index"]] = score

     # Increase the step
    state["step"] += 1
    state["question_index"] += 1

    # Return updated state
    return state, doc_to_save


def get_summary(message):
    summary_text = orchestrator.assistant.converse(prompt.SUMMARIZER, message)
    return summary_text


def reset_conversation_state():
    length_of_questions = len(BASE_QUESTIONS)
    return {"step": 0, "intro_done": False, "resume": "", 
            "questions": ["" for _ in range(length_of_questions)], 
            "answers": ["" for _ in range(length_of_questions)], 
            "question_index": 0}

