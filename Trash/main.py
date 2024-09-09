from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent

from langchain_openai import ChatOpenAI

import requests
from typing import List, Tuple, Annotated, TypedDict,Sequence
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

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

    feedback = state.get('feedback',[])
    if len(feedback) > 0:
        feedback = feedback[-1]
    else:
        feedback = ""

    html_code = state.get('html_code','')
  
    llm = ChatOpenAI(model="gpt-4o-mini",temperature = 0) #gpt 4o would give a better respone compared to mini

    tools = [TavilySearchResults(max_results=2)]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system","You are an experienced Web developer and have years of expertise in developing. rich and dynamic UIs. You are tasked with creating HTML and tailwind css for a new website."),
            ("system","The design team has provided you with the following input description: ```{input_description}```"),
            ("user","Here is some feedback from the evaluator ```{feedback}``` that must be incorporated to the existing HTML instead of recreating it. If no feedback is available, you could ignore."),
            ("system","IMPORTANT:GENERATE ONLY THE CODE AND NOTHING ELSE, DON'T GIVE ANY MARK UP OR EXPLANATIONS OR JUSTIFICATIONS SO THAT THE HTML CAN BE DIRECTLY DISPLAYED ON A WEBPAGE."),
            ("system","IMPORTANT: DO NOT INCLUDE ANY BACKTICKS AND DO NOT INCLUDE HTML INSIDE BACKTICKS LIKE ```html```."),
            MessagesPlaceholder(variable_name="messages"),
            ("system","Here is the previous HTML you already created ```{html_code}```"),
        ]
    ).partial(input_description=input_description,html_code = html_code,feedback=feedback)
    
    agent_executor = create_react_agent(llm, tools, messages_modifier=prompt)
    result = agent_executor.invoke({"messages": [("user", input_description)],"feedback":feedback,"html_code":html_code})
    return {'html_code': result["messages"][-1].content}
    

# Conditional edge to decide next step based on feedback
def decide_to_generate(state):
    print("---DECIDING NEXT STEP BASED ON FEEDBACK---")
    human_approval = state.get('human_approval',False)
    if not human_approval:
        return "human_intervention"
    else:
        return "generate_html_css"

# Node for human intervention
def human_intervention(state):
    print("---PERFORMING HUMAN INTERVENTION---")
    html_code = state['html_code']
    
    try:
        flask_response = requests.post('http://localhost:5000/display', data={'html_code': html_code})
        if flask_response.status_code == 200:
            print("HTML and CSS sent successfully to the Flask server.")
        else:
            print(f"Failed to send HTML and CSS to Flask server. Status code: {flask_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending HTML and CSS to Flask server: {e}")
        
    # Create a message asking for user feedback
    verification_message = f"Do you approve the design? Type 'APPROVED' if you do, or provide feedback."
    # Display the message to the user and capture their input
    user_input = input(verification_message)
    # Update the state based on user input
    if user_input == 'APPROVED':
        return {'human_approval': True, 'feedback': ['APPROVED']}
    else:
        return {'human_approval': False, 'feedback': [user_input]}
    
# Conditional edge to decide next step based on human intervention
def decide_based_on_human_intervention(state):
    print("---DECIDING NEXT STEP BASED ON HUMAN INTERVENTION---")
    if state['human_approval']:
        return "END"
    else:
        return "generate_html_css"

# Add nodes to the graph
graph.add_node("generate_html_css", generate_html_css)
# graph.add_node("search_web",search_web)
graph.add_node("human_intervention", human_intervention)

# graph.add_edge("search_web","generate_html_css")

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

# Compile the graph with interrupt before human_intervention
app = graph.compile()

# inputs = {
#     "messages": [
#         HumanMessage(
#             content="""Create a professional looking nav bar that has 4 elements namely Home,About Us, Our Services and Contact Us.\
#             Home should be at the left end of the Nav bar with a margin of 20px from the left. All other elements must be at the\
#             right end of the pane where the right most element has a margin of 20px from the right end. Elements at the right\
#             should have equal spacing between them."""
#         )
#     ]
#     }
# inputs = {
#     "messages": [
#         HumanMessage(
#             content="""Create a professional looking layout where I have two panels - a left panel and a right panel\
#             Left panel is a Nav Bar that has elements Home,About Us and Contact Us positioned vertically.\
#             These elements must be spread across the left pane all the way to the bottom of the page and\
#             they should have equal spacing betweem them.\
#             For the right panel, put a h2 title "Welcome User" with a form that captures user email, contact number and text area\
#             for comments.The layout should have great aesthetics and visual appeal as it will be used in a professional project."""
#         )
#     ]
#     }
# inputs = {
#     "messages": [
#         HumanMessage(
#             content="""Create a professional looking form that has 3 elements, an input field for email, an input field\
#             for password and another input field for password confirmation. There will be a Submit button as well. The form\
#             should have great aesthetics and visual appeal as it will be used in a professional project."""
#         )
#     ]
#     }
inputs = {
    "messages": [
        HumanMessage(
            content="""Create a professional webpage that has 3 main components. First componet is a Nav bar at the top that has 4 elements:\
            Home, About Us, Our Services and Contact Us. Home should be at the left end of the Nav bar whereas other 3 elements\
            should be at the far right. Home should have 20 px margin from the left end whereas Contact Us should have 20px margin from\
            the right end. Second component is a left pane that shows some text with a heading of h3. Third component is a \
            right pane that has two elements - a chat interface where in the top section the chat history appears(both human and ai responses)\
            and in the bottom section is where the user can type the question - so we need an input area and a Send button.\
            Both left pane and right pane should be nicely visually seperated and left pane should only take up 25 percentage of the total page width.\
            The webpage should have great aesthetics and visual appeal as it will be used in a professional project."""
        )
    ]
    }

import pprint


for output in app.stream(inputs):
        for key, value in output.items():
            pprint.pprint(f"Output from node '{key}':")
            pprint.pprint("---")
            pprint.pprint(value, indent=2, width=80, depth=None)
pprint.pprint("\n---\n")
    
