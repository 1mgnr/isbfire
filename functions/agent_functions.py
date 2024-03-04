
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


def agent_3_scorer(state, answer):

    base_question = BASE_QUESTIONS[state["question_index"]]

    state["answers"][state["question_index"]] = answer  # Save the candidate's answer
    
    print(f"\nReceived Candidate's Answer {state['question_index'] + 1}:\n{state['answers']}{state['question_index']}\n")  # Log answer to console
        
    score_string = orchestrator.assistant.converse(
        prompt.SCORER(base_question), f"Given the scoring guidelines mentioned above, please assess the following answer: {state['answers'][state['question_index']]}, with respect to the question: {state['questions'][state['question_index']]} and relevance to {base_question}. Give response in a json object with 1. final_score (number), 2. relevance_to_question (number), 3. seriousness_of_answer (number), 4. communication_skills (number), 5. the description, 6. base question: {base_question}, 7. question and 8. answer: {state['answers'][state['question_index']]}")
    
    print(f"\nAssessed Score for Question {state['question_index'] + 1}:\n{score_string}\n")  # Log score to console

    score_dict = json.loads(score_string)  # assuming the score_string is valid JSON

    # Calculate the weighted average
    final_score = (0.5 * score_dict["relevance_to_question"] +
                   0.3 * score_dict["seriousness_of_answer"] +
                   0.2 * score_dict["communication_skills"])
    
    if final_score > 2:
        is_satisfactory = True
    else:
        is_satisfactory = False
    
    state["scores"][state["question_index"]] = final_score

    # Increase the step
    state["step"] += 1
    state["question_index"] += 1

    # Form a dictionary with individual score and final score
    doc_to_save_dict = {"final_score": final_score, "individual_scores": score_dict, "is_satisfactory": is_satisfactory}

    # Convert dictionary to string
    doc_to_save = json.dumps(doc_to_save_dict)

    return state, doc_to_save , is_satisfactory


def get_summary(message):
    summary_text = orchestrator.assistant.converse(prompt.SUMMERISER, message)
    return summary_text


def reset_conversation_state():
    length_of_questions = len(BASE_QUESTIONS)
    return {"step": 0, "intro_done": False, "resume": "", 
            "questions": ["" for _ in range(length_of_questions)], 
            "answers": ["" for _ in range(length_of_questions)], 
            "question_index": 0}

