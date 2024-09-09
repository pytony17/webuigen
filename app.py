from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

app = Flask(__name__)
CORS(app)

# Store the HTML code globally
generated_html = ""

def generate_html_css(input_description, feedback="", html_code=""):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [TavilySearchResults(max_results=2)]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an experienced Web developer tasked with creating HTML and Tailwind CSS for a new website."),
        ("system", "The design team has provided you with the following input description: ```{input_description}```"),
        ("user", "Here is some feedback from the evaluator ```{feedback}``` that must be incorporated to the existing HTML instead of recreating it. If no feedback is available, you could ignore."),
        ("system", "IMPORTANT: GENERATE ONLY THE CODE AND NOTHING ELSE, DON'T GIVE ANY MARKUP OR EXPLANATIONS OR JUSTIFICATIONS SO THAT THE HTML CAN BE DIRECTLY DISPLAYED ON A WEBPAGE."),
        ("system", "IMPORTANT: DO NOT INCLUDE ANY BACKTICKS AND DO NOT INCLUDE HTML INSIDE BACKTICKS LIKE ```html```."),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Here is the previous HTML you already created ```{html_code}```"),
    ]).partial(input_description=input_description, html_code=html_code, feedback=feedback)
    
    agent_executor = create_react_agent(llm, tools, state_modifier=prompt)
    result = agent_executor.invoke({"messages": [("user", input_description)], "feedback": feedback, "html_code": html_code})
    return result["messages"][-1].content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    global generated_html
    if request.method == 'POST':
        description = request.json.get('description', '')
        generated_html = generate_html_css(description)
        return jsonify({"success": True, "message": "Web page generated successfully"})
    else:  # GET request
        return jsonify({"html": generated_html})

@app.route('/feedback', methods=['POST'])
def feedback():
    global generated_html
    feedback = request.json.get('feedback', '')
    if feedback == 'APPROVED':
        # Return both the message and the generated HTML/CSS
        return jsonify({
            "message": "Design approved!",
            "html": generated_html,
            "approved": True
        })
    else:
        generated_html = generate_html_css(input_description="", feedback=feedback, html_code=generated_html)
        return jsonify({
            "message": "Feedback incorporated",
            "html": generated_html,
            "approved": False
        })

@app.route('/display')
def display():
    global generated_html
    if not generated_html:  # Initialize with a default message if empty
        generated_html = "<p>No content generated yet.</p>"
    return render_template('display.html')

if __name__ == '__main__':
    app.run(debug=True)