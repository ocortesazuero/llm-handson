import streamlit as st
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from typing import Any
import os
import dotenv

dotenv.load_dotenv()
st.set_page_config(page_title="DigestPaper")

# Initialize OpenAI with the correct API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_file_path(uploaded_file):
    if uploaded_file is not None:
        file_path = os.path.join("temp", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        return file_path
    return None

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

# Streamlit app
st.title("Digest PDFs in one simple click!")

uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")

if uploaded_file is not None:
    # Get the uploaded file path
    file_path = get_file_path(uploaded_file)
    
    if file_path:
        st.write(f"File successfully saved at: {file_path}")

        # Create the vector store
        vector_store = client.beta.vector_stores.create(name="Paper summary")

        # Open and upload the PDF file correctly
        with open(file_path, "rb") as file_streams:
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[file_streams]  # Pass the file stream directly
            )

        # Display file batch status
        st.write("File batch successfully uploaded.")
        st.write(f"File batch status: {file_batch.status}")
        st.write(f"File count: {file_batch.file_counts}")

        # Create and configure the assistant
        assistant = client.beta.assistants.create(
            instructions="You are an expert researcher. Your goal is to summarise the document.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )

        # Create a thread with user instructions
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an expert researcher in the relevant domain. Summarise the document by extracting the key information in a structured and concise manner. Ensure you cover the following: \n"
                        "1. **Context and Motivation:** Briefly describe the research problem and why it is significant. \n"
                        "2. **Objective:** What are the main goals or questions addressed by the paper? \n"
                        "3. **Methods:** Summarise the key methods used to achieve the research objectives. \n"
                        "4. **Findings:** What are the major results of the study? \n"
                        "5. **Implications:** Discuss the broader impact of the findings or any applications.  \n"
                        "6. **Limitations and Future Work:** Note any key limitations and suggestions for future research. \n"
                        "Write the summary using neutral, formal academic language and keep it concise while retaining all essential details. Limit the overall length to 300–500 words. \n"
                        "If tables, figures, or supplementary material are provided, incorporate relevant insights if they are critical to the summary."
                    )
                }
            ],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )

        st.write("Thread created successfully.")

        # Run and fetch results
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant.id, timeout=1000
        )

        if run.status == "completed":
            messages_cursor = client.beta.threads.messages.list(thread_id=thread.id)
            messages = [message for message in messages_cursor]
            res_txt = messages[0].content[0].text.value
            st.write(res_txt)
        else:
            st.error(f"Run failed with status: {run.status}")

    else:
        st.error("Error: File path is invalid or not found.")
