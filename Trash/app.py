from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from typing import List, Tuple, Annotated, TypedDict, Sequence
import operator
from langgraph.graph import StateGraph, END

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store the HTML code globally
generated_html = ""

class State(TypedDict):
    input_description: str
    html_code: str
    feedback: Annotated[List[Tuple], operator.add]
    human_approval: bool
    messages: Annotated[Sequence[BaseMessage], operator.add]

graph = StateGraph(State)

def generate_html_css(state):
    print("---GENERATING HTML AND CSS---")
    input_description = state['messages'][-1].content
    feedback = state.get('feedback', [])
    feedback = feedback[-1] if feedback else ""
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
    return {'html_code': result["messages"][-1].content, 'human_approval': False}

def decide_next_step(state):
    print("---DECIDING NEXT STEP---")
    if state.get('human_approval', False):
        return "END"
    else:
        return "generate_html_css"

# Update the graph structure
graph.add_node("generate_html_css", generate_html_css)

graph.add_conditional_edges(
    "generate_html_css",
    decide_next_step,
    {
        "generate_html_css": "generate_html_css",
        "END": END,
    }
)

graph.set_entry_point("generate_html_css")
app_graph = graph.compile()

@app.route('/')
def index():
    return redirect(url_for('display_html_css'))

@app.route('/display', methods=['GET', 'POST'])
def display_html_css():
  global generated_html
  if request.method == 'GET':
      return render_template('display.html')
  elif request.method == 'POST':
      description = request.form.get('description', '')
      inputs = {
          "messages": [
              HumanMessage(content=description)
          ],
          "human_approval": False
      }
      output = generate_html_css(inputs)  # Call generate_html_css directly
      generated_html = output['html_code']
      output['human_approval'] = True  # Set human_approval to True
      return redirect(url_for('show_result'))
    
@app.route('/result')
def show_result():
    global generated_html
    return render_template('result.html', generated_html=generated_html)

@app.route('/feedback', methods=['POST'])
def feedback():
  global generated_html
  feedback = request.form['feedback']
  if feedback == 'APPROVED':
      return jsonify({"message": "Design approved!", "html": generated_html})
  else:
      # Only call generate_html_css if feedback is not "APPROVED"
      inputs = {
          "messages": [
              HumanMessage(content=feedback)
          ],
          "html_code": generated_html,
          "feedback": [feedback],
          "human_approval": False  # Initial state
      }
      for output_dict in app_graph.stream(inputs):  # Iterate through the single output
          if output_dict.get('generate_html_css') is not None:  # Check for key existence
              generated_html = output_dict['generate_html_css']['html_code']
              inputs['human_approval'] = True  # Set approval after update
              break  # Optional: Exit the loop after processing the single output
      return jsonify({"message": "Feedback incorporated", "html": generated_html})

if __name__ == '__main__':
    app.run(debug=True)