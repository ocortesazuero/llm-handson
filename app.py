import streamlit as st
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from typing import Any
import os
import dotenv

dotenv.load_dotenv()
st.set_page_config(page_title="DigestPaper")

def chat_response(system_prompt : str, user_prompt : str, model : str, temperature : float) -> str:
    client = OpenAI()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=400
    ).choices[0].message.content

    return response

def generate_abstract(topic : str) -> str:
    generation_system_prompt = load_template("./prompts/system.jinja", {})
    generation_user_prompt = load_template(
        "./prompts/user.jinja",
        {
            "topic": topic,
        }
    )

    fake_abstract = chat_response(generation_system_prompt, generation_user_prompt, "gpt-4o-mini", 0.2)

    return fake_abstract

def load_template(template_filepath: str, arguments: dict[str, Any]) -> str:
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__)) 
        # Set up the Jinja environment with the correct base path
        env = Environment(
            loader=FileSystemLoader(searchpath=current_dir),
            autoescape=select_autoescape()
        )
        template = env.get_template(template_filepath)
        return template.render(**arguments)

    except TemplateNotFound:
        st.error(f"Template file not found: {template_filepath}")
        return None
    
# Streamlit app
st.title("Digest PDFs in one simple click!")

topic = st.text_input("Enter a topic sentence:")
if st.button("Get PDF address"):
    if topic:
        #with st.spinner("Generating abstract..."):
         #   abstract = generate_abstract(topic)
        #st.subheader("Generated Abstract:")
        st.write(topic)
    else:
        st.warning("Please enter the path of a PDF file.")


# Add some information about the app
st.sidebar.header("About")
st.sidebar.info(
    "This app helps you digest complicated papers into easily understandable blog posts. Upload your PDF files and click on 'Generate summary' to process the paper(s)."
)

# streamlit run digester-app/app.py
