
def QUESTION_BUILDER(resume, base_question):

    return f'''Craft questions that delve into various facets of the candidate's experiences using their resume and base inquiries. 
    Avoid predictable lines of questioning; tailor inquiries to their educational background, projects, certifications, or employment 
    timeline. Ensure relevance and depth within 30 words. Utilize resume details such as work history, education, interests, relocation history, 
    or employment breaks to shape insightful questions. Maintain a tone of seasoned curiosity, reflecting the wisdom and simplicity of a 50-year-old self-made billionaire interviewer.
    Resume Snapshot: {resume}. Attribute: {base_question}. Make sure you ask only one question at a time. It should always be based on the attribute. Stick to the resume. And try not to ask question on topic which has been asked, but if you want to you can'''

def QUESTION_BUILDER_2(resume, base_question): 
    return f'''We want to assess the candidate's grit.
     We have their resume which is to be used as context, and a set of base questions.
     We can't directly ask base questions, as anyone can fool the system by selecting best option. 
     We need to be subjective, and frame a question based on the base question such that it is relavent to the resume and past experience.
     Ask targeted questions pertaining to things like projects, colleges, certifications, gaps in resumes or hobbies. Don't ask directly what is there in base question though.
     Here's RESUME MATTER: {resume}. And here's the BASE QUESTION/ATTRIBUTE: {base_question}. 
     Don't give it out in terms of what we want to be assessing. Make sure that you ask questions that are about the 
     candidate's experience across all things like college, hobbies, work experience, personal life etc, etc.
     The candidate must feel like someone is reading the resume and asking questions.
     Be smart and crisp (about 30 words or less) in asking the question. 
     Don't use the same keywords. Make sure that every question is relevant to some information provided in the resume like college,
     hobbies, work experience or certifications. Try to include questions beyond the candidate's work experience also.
     It should be a mix of college, hobbies, childhood town,migration to a big city/country etc etc in case you find these things on the resume.
     Don't go out of the realm of the resume ever. If you find a gap in resume, press hard on it. 
     If a person has migrated too frequently, use this nformation.
     No question can be a vanilla question regarding something in general'''

def QUESTION_BUILDER_3(resume, base_question): 
    return f'''Craft questions that delve into various aspects of the candidate's experiences using their 
    resume and base inquiries.Avoid predictable lines of questioning; tailor inquiries to their educational background, projects, 
    certifications, or employment timeline. Ensure relevance and depth within 30 words. Utilize resume details such as education, 
    interests, relocation history, or employment breaks to shape insightful questions. Stay within the scope of the resume.

    Resume Snapshot: {resume}. Attribute: {base_question}. Make sure you ask only one question at a time.
    It should always be based on the attribute. Stick to the resume.'''


def SCORER(base_question):  
    return f"Let's assess the candidate's response {base_question}. \n The scoring guidelines are as follows: 5 = Very much like me (Candidate has very clearly demonstrated how they overcame a significant challenge), 4 = Mostly like me (Candidate shows a fair amount of resilience in dealing with past difficulties), 3 = Somewhat like me (Candidate gives a somewhat fitting example of overcoming adversity), 2 = Not much like me (Candidate gives an example that doesn't quite demonstrate overcoming a major challenge), 1 = Not like me at all (Candidate does not provide a relevant example). Give zero points when there is one word answer and do not use N/A or anything which does not fit in json map format"


def INSIGHT_DISCOVERER(base_question):  
    f""

def RAPID_FIRE():
    f""

def CONVERSATION_MAKER():
    f""

SUMMERISER = f"please summarize the message in bullet point and try to contain major of the information with the facts and number and other info"


