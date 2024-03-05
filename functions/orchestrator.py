import json
import os
import openai
from dotenv import load_dotenv
import config
# assuming that prompts exist
import prompts

# Load environment variables from .env file
load_dotenv()

class OpenAIAssistant:
    def __init__(self):
        """Create a new OpenAI assistant."""
        self.openai_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.openai_key

    def converse(self, system_message, user_prompt):
        """Generate a response from the GPT-3 model."""
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
        )
        message = response.choices[0].message.content
        return message

class Orchestrator:
    def __init__(self, base_questions):
        """Create a new orchestrator with an instance of OpenAI assistant."""
        self.assistant = OpenAIAssistant()
        print(base_questions)

        self.state = {"step": 0, "intro_done": False, "resume": "", 
                      "questions": ["" for _ in range(len(base_questions))], 
                      "answers": ["" for _ in range(len(base_questions))], 
                      "question_index": 0,
                      "scores": ["" for _ in range(len(base_questions))]}  
        self.base_questions = base_questions         

    def agent_question_maker(self):
        base_question = self.base_questions[self.state['question_index']]
        self.state["questions"][self.state["question_index"]] = self.assistant.converse(prompts.QUESTION_BUILDER(self.state, base_question), 
                                                                                         f"Use the resume: {self.state['resume']}, previous Question: {self.state['questions']} generate a relevant question")
        self.state["step"] += 1
        return self.state

    def agent_scorer(self, answer):
        base_question = self.base_questions[self.state["question_index"]]
        self.state["answers"][self.state["question_index"]] = answer  # Save the candidate's answer

        score_string = self.assistant.converse(prompts.SCORER(base_question), 
                                               f"...description, 6. base question: {base_question}, 7. question and 8. answer: {self.state['answers'][self.state['question_index']]}")
        score_dict = json.loads(score_string)
        
        final_score = (0.5 * score_dict["relevance_to_question"] + 
                       0.3 * score_dict["seriousness_of_answer"] + 
                       0.2 * score_dict["communication_skills"])
        
        self.state["scores"][self.state["question_index"]] = final_score
        self.state["step"] += 1
        self.state["question_index"] += 1

        return self.state, final_score

    def get_summary(self, message):
        summary_text = self.assistant.converse(prompts.SUMMERISER, message)
        return summary_text

    def reset_state(self):
        length_of_questions = len(self.base_questions)
        self.state = {"step": 0, "intro_done": False, "resume": "", 
                    "questions": ["" for _ in range(length_of_questions)], 
                    "answers": ["" for _ in range(length_of_questions)], 
                    "question_index": 0,
                    "scores": ["" for _ in range(length_of_questions)]}