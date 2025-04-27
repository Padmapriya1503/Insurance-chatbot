import streamlit as st
import google.generativeai as genai
import json

# Step 1: Setup API Key
genai.configure(api_key='YOUR_API_KEY_HERE')  # Replace with your actual API key

# Step 2: Load Dataset
dataset_path = 'C://Users/HP/Downloads/bot/insurance.json'

with open(dataset_path, 'r') as f:
    dataset = json.load(f)

# Step 3: Build context from JSON
def build_context(query):
    context = ""

    query_lower = query.lower()

    for policy in dataset.get('policies', []):
        if query_lower in policy.get('policy_name', '').lower():
            context += f"Policy: {policy['policy_name']}\nCoverage: {policy['coverage']}\nExclusions: {policy['exclusions']}\nClaims Process: {policy['claims_process']}\n\n"

    for faq in dataset.get('faqs', []):
        if query_lower in faq.get('question', '').lower():
            context += f"Q: {faq['question']}\nA: {faq['answer']}\n\n"

    for user in dataset.get('users', []):
        if query_lower in user.get('name', '').lower():
            context += f"User: {user['name']}\nPolicy Held: {user['policy_held']}\nClaim Status: {user['claim_status']}\nRenewal Due: {user['renewal_due']}\n\n"

    return context

# Step 4: Initialize Gemini Model (only once)
@st.cache_resource
def load_model():
    model = genai.GenerativeModel('gemini-2.0-flash')
    chat = model.start_chat(history=[])
    return chat

chat = load_model()

# Step 5: Streamlit UI
st.title("🛡️ Insurance Chatbot (Powered by Gemini)")
st.write("Ask anything about your insurance policy, FAQs, or claims!")

# 🔹 Choose User Type
st.subheader("🔹 Choose User Type")

user_type = st.radio(
    "Are you a new or existing user?",
    ("New User", "Existing User")
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle New User (Direct Chat)
if user_type == "New User":
    st.subheader("💬 Ask anything about insurance")

    # Show existing chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask me anything...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        context = build_context(user_input)

        # If context found, add it; else just send user_input
        full_prompt = context + "\n" + user_input if context else user_input

        try:
            response = chat.send_message(full_prompt, stream=True)

            collected_text = ""
            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                for chunk in response:
                    if chunk.text:
                        collected_text += chunk.text
                        message_placeholder.markdown(collected_text + "▌")

                message_placeholder.markdown(collected_text)

            st.session_state.messages.append({"role": "assistant", "content": collected_text})

        except Exception as e:
            st.error(f"⚠️ An error occurred: {e}")

# Handle Existing User
elif user_type == "Existing User":
    user_id = st.text_input("Enter your User ID (e.g., U001, U002)")

    if user_id:
        user = next((u for u in dataset.get("users", []) if u["user_id"].lower() == user_id.lower()), None)

        if user:
            st.success(f"Welcome, {user['name']}!")

            policy = next((p for p in dataset.get('policies', []) if p['policy_name'] == user['policy_held']), None)

            st.markdown(f"""
                **Policy Held:** {user['policy_held']}
                
                - **Coverage Details:** {user['coverage_details']}
                - **Exclusions:** {user['exclusions']}
                - **Claim Status:** {user['claim_status']}
                - **Renewal Due:** {user['renewal_due']}
            """)

            if policy:
                st.markdown(f"**Claims Process:** {policy['claims_process']}")
            else:
                st.warning("⚠️ Claims Process not found.")

        else:
            st.error("❌ User ID not found. Please check and try again.")
