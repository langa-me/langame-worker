from flask import Request
import openai
import os

p = """conversation_starters = [('If you could have direct contact with human heart what would be your question?', ['ice breaker']),
 ('Who do you admire the most?', ['ice breaker']),
 ('What is the most amazing thing about humans that you have discovered?', ['mathematic', 'ice breaker']),
 ('If you could switch two colors when you drive stick on the pavement next to you/your head, where would they be?:', ['color']),
 ('What is all the meaning of life and what contributes to this meaning?', ['ice breaker']),
 ('Have you ever had a paranormal experience?', ['ice breaker']),
 ('What made you happy today?', ['ice breaker']),
 ('Who do you admire the most?', ['ice breaker']),
 ('What is something you did recently that was very beneficial for mental , physical or both well-being?', ['ice breaker']),
 ('What is the best piece of advice you have received?', ['ice breaker']),
 ('"Have you ever had one of those moments when you look back and realize you were a part of something so grand and so wonderful, you wish that you could go back to that moment and live it differently?"', ['mind', 'ice breaker']),
 ('What is the craziest thing you have ever seen someone do?', ['ice breaker']),
 ('What would you do if you were a billionaire  right now?', ['ice breaker']),
 ('From your experience, which seems like the more correct opinion between these two? "There are no absolute truth and everyone is right." or "There are absolute truth, one of the people is right."', ['philosophy', 'ice breaker']),
 ("What's something interesting your family would not understand?", ['ice breaker']),
 ('How do you save your sanity when the world is falling apart?', ['serendipity', 'ice breaker']),
 ('Are you happy with your hotel?', ['hotel', 'ice breaker']),
 ('What was the most difficult protest that youlied on?', ['ice breaker']),
 ('Where does a wish come from?', ['ice breaker']),
 ('What has been the most rewarding vacation you’ve taken?', ['ice breaker']),
 ('How was growing up different from your friends’s (average) childhood?', ['mind', 'ice breaker']),
 ("What do you love about your job? What's the worst part of it? What are your goals for this year and next?", ['ice breaker']),
 ('After studying history, what’s something you would change about the world as it is and why?', ['ice breaker']),
 ("What's the best piece of advice you've been given?", ['ice breaker']),
 ('What word do you most frequently use next to "problem"; and why?', ['ice breaker']),
 ('What are you currently practices or intentions for improvement?', ['ice breaker']),
 ('How many people would there need to be to amuse you at a meeting if everyone was wearing head cheese for a hat?', ['ice breaker']),
 ('What do you notice about people that left school without graduating?', ['ice breaker']),"""

def conversation_starter(_: Request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    openai.api_key = os.environ.get("OPENAI_KEY")
    openai.organization = os.environ.get("OPENAI_ORG")
    response = openai.Completion.create(
      engine="davinci-codex",
      prompt=p,
      temperature=1,
      max_tokens=100,
      top_p=1,
      frequency_penalty=0.7,
      presence_penalty=0,
      stop=["])"]
    )
    return {"output": response["choices"][0]["text"] + "]),"}
