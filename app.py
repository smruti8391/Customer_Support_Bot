import os
import json
import uuid
import streamlit as st
from google.oauth2 import service_account
from google.cloud import dialogflow_v2 as dialogflow

# Dialogflow Project ID
PROJECT_ID = "gpt-3-5chatbot-pawh"

# Access credentials from Streamlit secrets
credentials_json = st.secrets["google"]["gcp_credentials"]

# Parse the credentials from the secret (stored as a JSON string)
credentials_dict = json.loads(credentials_json)

# Authenticate Dialogflow using the service account credentials
credentials = service_account.Credentials.from_service_account_info(credentials_dict)


# Streamlit page settings
st.set_page_config(
    page_title="Customer Service Bot",
    page_icon="chatbot.png",
    layout="centered"
)

# Custom CSS for cleaner styling
st.markdown("""
    <style>
    .chat-container { max-width: 700px; margin: auto; padding: 10px; }
    .message { border-radius: 15px; padding: 10px 15px; margin: 5px 0; color: white; max-width: 80%; }
    .user-message { background-color: #34C759; float: right; text-align: right; }
    .assistant-message { background-color: #4F8BF9; float: left; text-align: left; }
    .chat-container::after { content: ""; clear: both; display: table; }
    .highlighted-option { border: 2px solid blue; border-radius: 10px; padding: 5px 10px; margin: 5px 0; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "option_selected" not in st.session_state:
    st.session_state.option_selected = False
if "started" not in st.session_state:
    st.session_state.started = False  # Track if "Start Chat" has been clicked

# Function to query Dialogflow
def get_dialogflow_response(user_query):
    session_client = dialogflow.SessionsClient(credentials=credentials)
    session = session_client.session_path(PROJECT_ID, st.session_state.session_id)
    text_input = dialogflow.TextInput(text=user_query, language_code="en")
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(session=session, query_input=query_input)
    return response.query_result.fulfillment_text

# Chat UI Header
st.markdown("""
    <h1 style='text-align: center;'>📱 Customer Support Bot</h1>
    <h3 style='text-align: center;'> Hello there! How can I assist you today?</h3>
""", unsafe_allow_html=True)

# Define the available options
options = ["Check What's New", "Check Order Status", "Return Policy", "Refund Policy", "Cancel Order", "Other"]

# Handle "back" functionality to reset the flow and show main options
user_query = st.chat_input("Type your query here...")

if user_query:
    # Handle 'back' functionality
    if user_query.strip().lower() == "back":
        # Reset chat history and show the main options after "back"
        st.session_state.chat_history = [{"role": "assistant", "content": "You're back to the main menu! Please select an option."}]
        st.session_state.option_selected = False  # Reset option selected status
        st.rerun()  # Re-run to reset chat flow and show options

    else:
        # Add user query to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Fetch and display response for custom query
        try:
            assistant_response = get_dialogflow_response(user_query)
        except Exception as e:
            assistant_response = f"Oops! Something went wrong: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

        # Re-run to display new chat history
        st.rerun()

# Custom CSS to center "Start Chat" button
st.markdown("""
    <style>
    .start-chat-btn {
        text-align: center;
        margin-top: 30px; /* Adds some spacing between the header and the button */
    }
    </style>
""", unsafe_allow_html=True)

# Create three columns: left, middle, and right
left, middle, right = st.columns(3)

# Show the 'Start Chat' button centered
if not st.session_state.started:
    st.markdown('<div class="start-chat-btn">', unsafe_allow_html=True)
    if middle.button("Start Chat"):
        # Query Dialogflow for start chat message (greeting, etc.)
        start_chat_response = get_dialogflow_response("Start Chat")
        
        # Add Dialogflow's response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": start_chat_response})
        
        # After showing Dialogflow's response, show the main options
        st.session_state.started = True  # Set flag to True after "Start Chat" is clicked
        st.rerun()  # Re-run to show main options
    st.markdown('</div>', unsafe_allow_html=True)

# Show options after "Start Chat" and option selected
if st.session_state.started and not st.session_state.option_selected:
    st.markdown('<div class="option-grid">', unsafe_allow_html=True)
    for option in options:
        if st.button(option, key=option):
            st.session_state.chat_history.append({"role": "user", "content": option})  # Add user message

            # Fetch and display assistant response for the selected option
            dialogflow_response = get_dialogflow_response(option)
            st.session_state.chat_history.append({"role": "assistant", "content": dialogflow_response})

            # Mark the option as selected
            st.session_state.option_selected = True  # Set flag to True after selecting an option

            # Ensure the assistant's response is displayed without rerun
            st.rerun()  # Refresh UI to display the response after the option is clicked
    st.markdown('</div>', unsafe_allow_html=True)

# Display chat history above the input field
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.chat_history:
    role_class = "user-message" if message["role"] == "user" else "assistant-message"
    st.markdown(f'<div class="message {role_class}">{message["content"]}</div><br><br>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
