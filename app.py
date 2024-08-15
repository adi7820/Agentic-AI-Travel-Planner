import streamlit as st
import asyncio
from autogen import AssistantAgent, UserProxyAgent
import os
import autogen
from llama_index.core import Settings
from llama_index.core.agent import ReActAgent
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.tools.wikipedia import WikipediaToolSpec
from autogen.agentchat.contrib.llamaindex_conversable_agent import LLamaIndexConversableAgent
import queue
import time

# Initialize Streamlit
st.title("_Agentic_ AI :blue[Trip] Planner✈️")

# def response_generator(response):
#     for word in response.split():
#         yield word + " "
#         time.sleep(0.05)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


config_list = [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY")}]

# class TrackableAssistantAgent(LLamaIndexConversableAgent):
#     def _process_received_message(self, message, sender, silent):
#         st.session_state.messages.append({"role": "user", "content": message["content"]})
#         with st.chat_message("User"):
#             st.markdown(message["content"])
#         return super()._process_received_message(message, sender, silent)

# class TrackableUserProxyAgent(UserProxyAgent):
#     def _process_received_message(self, message, sender, silent):
#         with st.chat_message("Assistant"):
#             st.markdown(message["content"])
#         st.session_state.messages.append({"role": "assistant", "content": message["content"]})
#         return super()._process_received_message(message, sender, silent)


def user_print_messages_callback(recipient, messages, sender, config):     
    message = messages[-1]
    split_text = message["content"].split("Context:")
    st.session_state.messages.append({"role": "user", "content": split_text[0]})
    with st.chat_message("User"):
        st.markdown(split_text[0])

    return False, None  # required to ensure the agent communication flow continues

def assistant_print_messages_callback(recipient, messages, sender, config):     
    message = messages[-1]

    st.session_state.messages.append({"role": "assistant", "content": message["content"]})
    st.session_state.history = message["content"]
    with st.chat_message("Assistant"):
        st.markdown(message["content"])

    return False, None  # required to ensure the agent communication flow continues

selected_model = None
selected_key = None
with st.sidebar:
    st.header("OpenAI Configuration")
    selected_model = st.selectbox("Model", ['gpt-4o-mini', 'gpt-4-turbo', 'gpt-4o', 'gpt-3.5-turbo'], index=0)
    selected_key = st.text_input("API Key", type="password")



# Initialize the LLM and Embedding Models
llm = OpenAI(
    model=selected_model,
    temperature=0.0,
    api_key=selected_key,
)

embed_model = OpenAIEmbedding(
    model="text-embedding-ada-002",
    api_key=selected_key,
)

# Apply settings
Settings.llm = llm
Settings.embed_model = embed_model

# Initialize Wikipedia Tool and ReAct Agent
wiki_spec = WikipediaToolSpec()
# Get the search wikipedia tool
wikipedia_tool = wiki_spec.to_tool_list()[1]

location_specialist = ReActAgent.from_tools(tools=[wikipedia_tool], llm=llm, max_iterations=10, verbose=True)

llm_config = {
    "temperature": 0,
    "config_list": config_list,
}

trip_assistant = LLamaIndexConversableAgent(
    "trip_specialist",
    llama_index_agent=location_specialist,
    system_message="You help customers finding more about places they would like to visit. You can use external resources to provide more details as you engage with the customer.",
    description="This agents helps customers discover locations to visit, things to do, and other details about a location. It can use external resources to provide more details. This agent helps in finding attractions, history and all that there is to know about a place",
    
)

user_proxy = autogen.UserProxyAgent(
    name="Admin",
    human_input_mode="ALWAYS",
    code_execution_config=False,
    is_termination_msg=lambda msg: "good bye" in msg["content"].lower()
)

user_proxy.register_reply(
    [autogen.Agent, None],
    reply_func=assistant_print_messages_callback
)

trip_assistant.register_reply(
    [autogen.Agent, None],
    reply_func=user_print_messages_callback
)


groupchat = autogen.GroupChat(
    agents=[trip_assistant, user_proxy],
    messages=[],
    max_round=500,
    speaker_selection_method="round_robin",
    enable_clear_history=False,
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

user_input = st.chat_input("Type your trip query...")
if user_input:
    if not selected_key or not selected_model:
        st.warning('You must provide a valid OpenAI API key and choose a preferred model', icon="⚠️")
        st.stop()

chat_result = user_proxy.initiate_chat(
        manager,
        message=user_input,
        clear_history=False,
        carryover=st.session_state.history
    )

# result = user_proxy.initiate_chat(manager, message=user_input)

        # Add the user and assistant messages to the session state
        
        # Example: Append the assistant's response (assuming `assistant_response` is what it returned)

# Display chat history
# for message in st.session_state["messages"]:
#     with st.chat_message(message["sender"]):
#         st.markdown(message["content"])


