from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent

from langchain_openai import ChatOpenAI

import requests
from typing import List, Tuple, Annotated, TypedDict, Sequence
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

class State(TypedDict):
    input_description: str
    html_code: str
    feedback: Annotated[List[Tuple], operator.add]
    human_approval: bool
    messages: Annotated[Sequence[BaseMessage], operator.add]

graph = StateGraph(State)

# Node for HTML and CSS generation
def generate_html_css(state):
    print("---GENERATING HTML AND CSS---")
    input_description = state['messages'][-1].content

    feedback = state.get('feedback', [])
    if len(feedback) > 0:
        feedback = feedback[-1]
    else:
        feedback = ""

    html_code = state.get('html_code', '')
  
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    tools = [TavilySearchResults(max_results=2)]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an experienced Web developer and have years of expertise in developing rich and dynamic UIs. You are tasked with creating HTML and tailwind css for a new website."),
            ("system", "The design team has provided you with the following input description: ```{input_description}```"),
            ("user", "Here is some feedback from the evaluator ```{feedback}``` that must be incorporated to the existing HTML instead of recreating it. If no feedback is available, you could ignore."),
            ("system", "IMPORTANT:GENERATE ONLY THE CODE AND NOTHING ELSE, DON'T GIVE ANY MARK UP OR EXPLANATIONS OR JUSTIFICATIONS SO THAT THE HTML CAN BE DIRECTLY DISPLAYED ON A WEBPAGE."),
            ("system", "IMPORTANT: DO NOT INCLUDE ANY BACKTICKS AND DO NOT INCLUDE HTML INSIDE BACKTICKS LIKE ```html```."),
            MessagesPlaceholder(variable_name="messages"),
            ("system", "Here is the previous HTML you already created ```{html_code}```"),
        ]
    ).partial(input_description=input_description, html_code=html_code, feedback=feedback)
    
    agent_executor = create_react_agent(llm, tools, state_modifier=prompt)
    result = agent_executor.invoke({"messages": [("user", input_description)], "feedback": feedback, "html_code": html_code})
    return {'html_code': result["messages"][-1].content}

# Conditional edge to decide next step based on feedback
def decide_to_generate(state):
    print("---DECIDING NEXT STEP BASED ON FEEDBACK---")
    human_approval = state.get('human_approval', False)
    if not human_approval:
        return "human_intervention"
    else:
        return "generate_html_css"

# Node for human intervention
def human_intervention(state):
    print("---PERFORMING HUMAN INTERVENTION---")
    html_code = state['html_code']
    
    # Instead of sending to a separate Flask server, we'll use the current app
    global generated_html
    generated_html = html_code
    
    # We'll handle user input in the Flask route, so we'll just return here
    return {'human_approval': False, 'feedback': []}

# Conditional edge to decide next step based on human intervention
def decide_based_on_human_intervention(state):
    print("---DECIDING NEXT STEP BASED ON HUMAN INTERVENTION---")
    if state['human_approval']:
        return "END"
    else:
        return "generate_html_css"

# Add nodes to the graph
graph.add_node("generate_html_css", generate_html_css)
graph.add_node("human_intervention", human_intervention)

graph.add_conditional_edges(
    "generate_html_css",
    decide_to_generate,
    { 
        "human_intervention": "human_intervention", 
         "generate_html_css": "generate_html_css",     
    }   
)
graph.add_conditional_edges(
    "human_intervention",
    decide_based_on_human_intervention, 
    {
        "generate_html_css": "generate_html_css",
        "END": END, 
    }
)

# Set the entry point for the graph
graph.set_entry_point("generate_html_css")

# Compile the graph
app_graph = graph.compile()

# Global variable to store generated HTML
generated_html = ""

@app.route('/', methods=['GET', 'POST'])
def index():
    global generated_html
    if request.method == 'POST':
        description = request.form['description']
        inputs = {
            "messages": [
                HumanMessage(content=description)
            ]
        }
        for output in app_graph.stream(inputs):
            for key, value in output.items():
                if key == 'generate_html_css':
                    generated_html = value['html_code']
        return render_template('result.html', generated_html=generated_html)
    return render_template('display.html')

@app.route('/feedback', methods=['POST'])
def feedback():
    global generated_html
    feedback = request.form['feedback']
    if feedback == 'APPROVED':
        return jsonify({"message": "Design approved!", "html": generated_html})
    else:
        inputs = {
            "messages": [
                HumanMessage(content=feedback)
            ],
            "html_code": generated_html,
            "feedback": [feedback]
        }
        for output in app_graph.stream(inputs):
            for key, value in output.items():
                if key == 'generate_html_css':
                    generated_html = value['html_code']
        return jsonify({"message": "Feedback incorporated", "html": generated_html})

if __name__ == '__main__':
    app.run(debug=True)