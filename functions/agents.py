
import json
from config import *
from orchestrator import Orchestrator, OpenAIAssistant  # import necessary classes
import prompts as prompt

assistant = OpenAIAssistant()  # instantiate the assistant
orchestrator = Orchestrator(assistant)  # instantiate the orchestrator


def agent_1_question_maker(resume, current_index):
    # Get the base question first
    if current_index < len(BASE_QUESTIONS):
        base_question = BASE_QUESTIONS[current_index]
        question = orchestrator.assistant.converse(
                    prompt.QUESTION_BUILDER(resume, base_question), f"Use the resume: {resume}, and base question {base_question} generate a relevant question")
        return question
    else:
        return None


def agent_2_followup_question_maker(index):
    # Get the base question first
    base_question = BASE_QUESTIONS[index]
    
    # The rest of this function stays essentially the same
    question = orchestrator.assistant.converse(prompt.QUESTION_BUILDER(state, base_question), f"Use the resume: {state['resume']}, previous Question: {state['questions']} generate a relevant question")
    
    # Return updated state
    return question

# def weighted_score(score_dict, weights):
#     """
#     Gives a weighted score based on weights provided.
#     """
#     weighted_scores = {k: score_dict[k]*weights[k] for k in score_dict}
#     return sum(weighted_scores.values())


def agent_3_scorer(answer, question, question_index):

    base_question = BASE_QUESTIONS[question_index]
    
    weights = {"relevance": 0.4, "sincerity": 0.3, "communication_skills": 0.3}  # define your own weights

    # Assuming prompt.SCORER is a properly formatted string to prompt the scoring process
    prompt_message = f"Given the scoring guidelines mentioned above, please assess the following answer: {answer}, " + \
        f"with respect to the question: {question} and relevance to {BASE_QUESTIONS[question_index]}. " + \
        "If the answer is one word, give lower points. " + \
        "Give response in a json object following keys: relevance, sincerity, communication_skills, " + \
        f"score (weighted sum based on {weights}), base_question: {BASE_QUESTIONS[question_index]}, " + \
        f"answer: {answer}, question: {question}, " + \
        "description (rationale of scoring based on relevance, sincerity, and communication skills)"
    
    score_dict_str = orchestrator.assistant.converse(prompt.SCORER(base_question), prompt_message)
    score_dict = json.loads(score_dict_str)

    print(f"Assessed Score for Question {question_index + 1}:\n{score_dict}\n")  # Log score to console

    # Prepare document to save
    doc_to_save = score_dict
    
    is_satisfactory=True

    if score_dict["score"] < 2:
        is_satisfactory = False

    is_satisfactory = score_dict["score"] >= 2
    return score_dict, doc_to_save, is_satisfactory



def get_summary(message):
    summary_text = orchestrator.assistant.converse(prompt.SUMMERISER, message)
    return summary_text


def reset_conversation_state():
    return {"step": 0,
        "intro_done": False,
        "resume": "",
        "interview": [],  # Stores QA pairs
        "current_q_index": 0 }

