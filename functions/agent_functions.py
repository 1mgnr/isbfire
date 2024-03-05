
import json
from config import *
from orchestrator import Orchestrator, OpenAIAssistant  # import necessary classes
import prompts as prompt

assistant = OpenAIAssistant()  # instantiate the assistant
orchestrator = Orchestrator(assistant)  # instantiate the orchestrator


def agent_1_question_maker(state):
    # Get the base question first
    base_question = BASE_QUESTIONS[state['question_index']]
    
    # The rest of this function stays essentially the same
    state["questions"][state["question_index"]] = orchestrator.assistant.converse(prompt.QUESTION_BUILDER(state, base_question), f"Use the resume: {state['resume']}, previous Question: {state['questions']} generate a relevant question")
    
    # Increase the step
    state["step"] += 1
    
    # Return updated state
    return state


# def weighted_score(score_dict, weights):
#     """
#     Gives a weighted score based on weights provided.
#     """
#     weighted_scores = {k: score_dict[k]*weights[k] for k in score_dict}
#     return sum(weighted_scores.values())


def agent_3_scorer(state, answer):

    base_question = BASE_QUESTIONS[state["question_index"]]
    state["answers"][state["question_index"]] = answer  # Save the candidate's answer
    print(f"\nReceived Candidate's Answer {state['question_index'] + 1}:\n{state['answers']}{state['question_index']}\n")  # Log answer to console
    
    weights = {"relevance": 0.4, "sincerity": 0.3, "communication_skills": 0.3}  # define your own weights

    score_dict = orchestrator.assistant.converse(
        prompt.SCORER(base_question), f"Given the scoring guidelines mentioned above, please assess the following answer: {state['answers'][state['question_index']]}, with respect to the question: {state['questions'][state['question_index']]} and relevance to {base_question}. If answer is one worder give lower points. Give response in a json object following keys: relevance, sincerity, communication_skills, score (weighted sum based on {weights}), base_question: {base_question}, answer:{state['answers'][state['question_index']]}, question:{state['questions'][state['question_index']]}, description (rationalie of scoring based in relevance, sincerity and communication skills)")
    
    print(f"\nAssessed Score for Question {state['question_index'] + 1}:\n{score_dict}\n")  # Log score to console

    # weighted_score_total = weighted_score(score_dict, weights)

    score_json = json.loads(score_dict)

    # Prepare document to save
    doc_to_save = score_dict
    
    state["scores"][state["question_index"]] = score_json["score"]

     # Increase the step
    state["step"] += 1
    state["question_index"] += 1

    is_satisfactory=True

    # Return updated state
    return state, doc_to_save, is_satisfactory


def get_summary(message):
    summary_text = orchestrator.assistant.converse(prompt.SUMMERISER, message)
    return summary_text


def reset_conversation_state():
    length_of_questions = len(BASE_QUESTIONS)
    return {"step": 0, "intro_done": False, "resume": "", 
            "questions": ["" for _ in range(length_of_questions)], 
            "answers": ["" for _ in range(length_of_questions)], 
            "question_index": 0}

