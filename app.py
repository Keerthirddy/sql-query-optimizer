import streamlit as st
import os
from langchain_openrouter import ChatOpenRouter

# ✅ Get API key
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    api_key = st.secrets["OPENROUTER_API_KEY"]

os.environ["OPENROUTER_API_KEY"] = api_key

# ✅ Model
model = ChatOpenRouter(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    temperature=0
)

# ✅ Detect if input is SQL
def is_sql_query(text):
    keywords = ["select", "insert", "update", "delete", "create", "with"]
    return any(word in text.lower() for word in keywords)

# ✅ SQL Optimizer
def optimize_sql(user_input):
    prompt = f"""
You are a Snowflake SQL expert.

Strict rules:
- ALWAYS fully optimize the query
- NEVER keep functions on columns in WHERE
- ALWAYS remove subqueries using JOIN
- NEVER use SELECT *
- Convert date filters into ranges

ALWAYS follow EXACT format:

OPTIMIZED_QUERY:
<SQL>

IMPROVEMENTS:
- points

BEST_PRACTICES:
- points

Query:
{user_input}
"""

    try:
        response = model.invoke([
            {"role": "user", "content": prompt}
        ])
        return response.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# ✅ Normal Chat
def normal_chat(user_input):
    prompt = f"""
You are a friendly assistant.

Respond normally.

At the end say:
"I’m designed to optimize SQL queries. Feel free to share one!"

User:
{user_input}
"""

    try:
        response = model.invoke([
            {"role": "user", "content": prompt}
        ])
        return response.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# ---------------- UI ---------------- #

st.set_page_config(page_title="SQL Optimizer", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #F5F7FA;
}
.block-container {
    padding-top: 2rem;
}
.title {
    text-align: center;
    font-size: 26px;
    font-weight: 600;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">SQL Query Optimizer 📊</div>', unsafe_allow_html=True)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
user_input = st.chat_input("Paste your SQL query here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        if is_sql_query(user_input):
            st.code(user_input, language="sql")
        else:
            st.markdown(user_input)

    if is_sql_query(user_input):
        response = optimize_sql(user_input)

        # 🔥 SAFE PARSING
        optimized = ""
        improvements = ""
        best = ""

        if "OPTIMIZED_QUERY:" in response:
            parts = response.split("OPTIMIZED_QUERY:")
            if len(parts) > 1:
                rest = parts[1]

                if "IMPROVEMENTS:" in rest:
                    sections = rest.split("IMPROVEMENTS:")
                    optimized = sections[0]

                    if len(sections) > 1:
                        sub = sections[1]

                        if "BEST_PRACTICES:" in sub:
                            sub_parts = sub.split("BEST_PRACTICES:")
                            improvements = sub_parts[0]
                            if len(sub_parts) > 1:
                                best = sub_parts[1]
                        else:
                            improvements = sub
                else:
                    optimized = rest

        # 🔥 DISPLAY
        with st.chat_message("assistant"):

            if optimized.strip():
                st.markdown("### ⚡ Optimized Query")
                st.code(optimized.strip(), language="sql")
            else:
                st.markdown(response)  # fallback

            if improvements.strip():
                st.markdown("### 🔧 Improvements")
                st.markdown(improvements.strip())

            if best.strip():
                st.markdown("### ❄️ Snowflake Best Practices")
                st.markdown(best.strip())

    else:
        response = normal_chat(user_input)

        with st.chat_message("assistant"):
            st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
