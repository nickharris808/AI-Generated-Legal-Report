import streamlit as st
import pandas as pd
import json
import openai
from openai import OpenAI
from jsonschema import validate, ValidationError
import PyPDF2
from docx import Document
from PIL import Image
import tiktoken
import textract
import os
import tempfile
import datetime
from datetime import datetime
import requests
from pymongo import MongoClient
from bson.binary import Binary
import time
import requests
from bs4 import BeautifulSoup

client = OpenAI()


openai.api_key = os.environ.get('OPENAI_API_KEY')

def process_uploaded_files(files):
    """Process all uploaded files using textract and return their contents."""
    if not files:
        return []
    
    extracted_contents = []
    
    for file in files:
        try:
            # Create a temporary file with the original extension
            with tempfile.NamedTemporaryFile(delete=False, suffix='.'+file.name.split('.')[-1]) as temp_file:
                # Write the uploaded file's content to the temporary file
                temp_file.write(file.getvalue())
                temp_file_path = temp_file.name
            
            # Process the file with textract
            try:
                content = textract.process(temp_file_path).decode('utf-8')
                extracted_contents.append({
                    'name': file.name,
                    'content': content  # Limit each file to 1000 tokens
                })
            except Exception as e:
                extracted_contents.append({
                    'name': file.name,
                    'content': f"Error extracting content: {str(e)}"
                })
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            extracted_contents.append({
                'name': file.name,
                'content': f"Error processing file: {str(e)}"
            })
    
    return extracted_contents


def generate_report_with_openai(user_inputs, arizona_laws, medical_literature):

    # Process all uploaded files (both documents and photos) at once
    all_files = (user_inputs.get('documents', []) or []) + (user_inputs.get('photos', []) or [])
    processed_files = process_uploaded_files(all_files)
    
    # # Truncate incident overview
    incident_overview = user_inputs.get('incident_overview', '')  

    """Generate a comprehensive report using OpenAI, combining Arizona laws and medical literature."""
    
    # Format Arizona laws and medical literature as text
    arizona_law_text = "\n".join([f"- {law['title']}: {law['snippet']} (Link: {law['link']})" for law in arizona_laws])
    medical_literature_text = "\n".join([f"- {paper['title']}: {paper['snippet']} (Link: {paper['link']})" for paper in medical_literature])

    # Format Arizona laws and medical literature as detailed text with content included
    arizona_law_text = "\n\n".join([
        f"<b>{law['title']}</b>:<br>{law['content']}<br><a href='{law['link']}'>Read more</a>"
        for law in arizona_laws
    ])

    medical_literature_text = "\n\n".join([
        f"<b>{paper['title']}</b>:<br>{paper['content']}<br><a href='{paper['link']}'>Read more</a>"
        for paper in medical_literature
])

    prompt = f"""
    Generate a detailed and thorough legal report in HTML format based on the provided information. Ensure the report includes all relevant legal statutes, case precedents, and medical information crucial to the case, without omitting any essential details.

    **Client Information:**
    - Client Name: {user_inputs.get('client_name')}
    - Incident Date: {user_inputs.get('incident_date')}
    - Contact Information: {user_inputs.get('contact_info', 'N/A')}

    **Incident Overview:**
    {incident_overview}

    **Processed Files:**
    {json.dumps(processed_files, indent=2)}

    **Estimated Compensation:**
    - Economic Damages: ${user_inputs.get('economic_damages', 0)}
    - Non-Economic Damages: ${user_inputs.get('non_economic_damages', 0)}
    - Punitive Damages: ${user_inputs.get('punitive_damages', 0)}

    **Relevant Arizona Laws:**
    {arizona_law_text}

    **Relevant Medical Literature:**
    {medical_literature_text}

    Please produce the output as valid HTML without Markdown formatting, code blocks, or any extra symbols. Structure the report according to the following sections and fields, providing detailed explanations where applicable:

    - **Client Information**: Name, Incident Date, and Contact Info.
    - **Incident Overview**: A clear, thorough summary of the incident and its circumstances.
    - **Document Analysis**: For each processed file, include:
    - **File Name**: Name of the file.
    - **Key Points**: A concise list of the most critical points or findings.
    - **Relevance**: Explanation of how this document supports or impacts the case.
    - **Legal Analysis**:
    - **Applicable Laws**: Detailed list of relevant laws, statutes, and legal precedents.
    - **Case Strength**: Assessment of the case’s overall strength and viability.
    - **Legal Arguments**: Comprehensive list of potential legal arguments, tailored to this specific case.
    - **Damages Assessment**:
    - **Economic Damages**: Value and breakdown.
    - **Non-Economic Damages**: Value and explanation.
    - **Punitive Damages**: Value and rationale.
    - **Total Valuation**: Summed total of damages.
    - **Explanation**: Detailed reasoning behind each damage assessment.
    - **Action Plan**: Suggested steps and strategies for moving forward with the case.
    - **Conclusion**: Summarize the case’s potential outcome, considering all gathered evidence, legal analysis, and medical insights.

    The report should be well-structured to provide clarity to both legal and non-legal readers. Output must be in valid HTML, adhering strictly to the format above, with no extra symbols, Markdown syntax, or code blocks.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable legal assistant. Generate a detailed legal report based on the provided information, formatted as valid HTML without Markdown syntax or code blocks."},
                {"role": "user", "content": prompt}
            ],
        )
        html_content = response.choices[0].message.content.strip()
        return html_content

    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
        return None



def fetch_arizona_laws(query):
    """Automatically search for the top 5 Arizona laws/cases and scrape their full content."""
    full_query = f"{query} Arizona law"
    params = {
        "q": full_query,
        "engine": "google_scholar",
        "api_key": "your_serpapi_key_here"
    }
    response = requests.get("https://serpapi.com/search", params=params)
    arizona_laws = []
    
    if response.status_code == 200:
        results = response.json().get('organic_results', [])
        
        for idx, result in enumerate(results):
            if idx >= 5:  # Limit to the top 5 articles or cases
                break
            
            title = result['title']
            link = result['link']
            
            # Fetch and parse the full article content from the link
            try:
                law_response = requests.get(link)
                law_soup = BeautifulSoup(law_response.text, 'html.parser')
                
                # Example: Attempt to extract the main content from common tags used in legal articles or cases
                paragraphs = law_soup.find_all(['p', 'section', 'div'])
                full_content = "\n".join(p.get_text() for p in paragraphs if p.get_text())
                
                # Append the content along with other metadata
                arizona_laws.append({
                    'title': title,
                    'link': link,
                    'content': full_content or "Content could not be fetched."
                })
            except Exception as e:
                arizona_laws.append({
                    'title': title,
                    'link': link,
                    'content': f"Error fetching content: {e}"
                })
    return arizona_laws


def fetch_medical_literature(query):
    """Automatically search for the top 5 relevant medical articles and scrape their full content."""
    full_query = f"{query} medical"
    params = {
        "q": full_query,
        "engine": "google",
        "api_key": "c0fcb889fa2864af3d0b423adb345b8901feb48d807adfc5a908d6632f89398d"
    }
    response = requests.get("https://serpapi.com/search", params=params)
    medical_literature = []
    
    if response.status_code == 200:
        results = response.json().get('organic_results', [])
        
        for idx, result in enumerate(results):
            if idx >= 5:  # Stop after the top 5 articles
                break
            
            title = result['title']
            link = result['link']
            
            # Fetch and parse the full article from each URL
            try:
                article_response = requests.get(link)
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Example: Try to extract the main content from common tags used for articles
                paragraphs = article_soup.find_all(['p', 'article', 'div'])
                full_content = "\n".join(p.get_text() for p in paragraphs if p.get_text())
                
                # Append the full content along with other metadata
                medical_literature.append({
                    'title': title,
                    'link': link,
                    'content': full_content or "Content could not be fetched."
                })
            except Exception as e:
                medical_literature.append({
                    'title': title,
                    'link': link,
                    'content': f"Error fetching content: {e}"
                })
    return medical_literature




# Connect to MongoDB
def get_mongo_client():
    client = MongoClient("mongodb://localhost:27017/")  # Change this for MongoDB Atlas if needed
    db = client["legal_reports_db"]  # Create or connect to the database
    return db


# Store file in MongoDB without GridFS for files less than 16MB
def store_file_in_mongodb(file, user_id, db, collection_name="files"):
    """Store file as binary data in a MongoDB collection with metadata."""
    metadata = {
        "filename": file.name,
        "filetype": file.type,
        "user_id": user_id,
        "uploaded_at": time.time(),
        "filedata": Binary(file.getvalue())  # Store the file content as binary data
    }

    # Insert the file and its metadata into the collection
    file_id = db[collection_name].insert_one(metadata).inserted_id
    return file_id

def store_report_in_mongodb(report_html, user_id, db, collection_name="reports"):
    """Store generated HTML report with metadata."""
    report = {
        "user_id": user_id,
        "report_html": report_html,
        "created_at": time.time()
    }
    report_id = db[collection_name].insert_one(report).inserted_id
    return report_id

def get_reports_by_user_id(user_id, db, collection_name="reports"):
    """Retrieve all reports by user_id."""
    reports = db[collection_name].find({"user_id": user_id})
    return list(reports)

def get_files_by_user_id(user_id, db, collection_name="files"):
    """Retrieve all files by user_id."""
    # fs = gridfs.GridFS(db)
    # files = fs.find({"metadata.user_id": user_id})
    files = db[collection_name].find({"user_id": user_id})
    return list(files)


# Main Streamlit app
def main():
    st.set_page_config(page_title="AI-Generated Legal Report", layout="wide")
    st.title("AI-Legal Report Generator")

    # Initialize MongoDB connection
    db = get_mongo_client()

    # Initialize session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'user_inputs' not in st.session_state:
        st.session_state.user_inputs = {}

    if st.session_state.step == 1:
        st.header("Step 1: Client Information")
        with st.form(key='step1_form'):
            user_id = st.text_input("User ID", value="1234")  # Placeholder for user ID
            client_name = st.text_input("Client Name", value=st.session_state.user_inputs.get('client_name', ''))
            incident_date = st.date_input("Incident Date", value=pd.to_datetime(st.session_state.user_inputs.get('incident_date', '2024-01-01')))
            contact_info = st.text_input("Contact Information (Optional)", value=st.session_state.user_inputs.get('contact_info', ''))
            submit_step1 = st.form_submit_button("Next")

        if submit_step1:
            if not client_name or not incident_date:
                st.warning("Please provide both Client Name and Incident Date.")
            else:
                st.session_state.user_inputs['user_id'] = user_id
                st.session_state.user_inputs['client_name'] = client_name
                st.session_state.user_inputs['incident_date'] = incident_date.strftime('%Y-%m-%d')
                st.session_state.user_inputs['contact_info'] = contact_info
                st.session_state.step = 2
            st.rerun()

    elif st.session_state.step == 2:
        st.header("Step 2: Incident Overview")
        with st.form(key='step2_form'):
            incident_overview = st.text_area("Describe what happened in detail:", value=st.session_state.user_inputs.get('incident_overview', ''))
            submit_step2 = st.form_submit_button("Next")

        if submit_step2:
            if not incident_overview:
                st.warning("Please provide a detailed Incident Overview.")
            else:
                st.session_state.user_inputs['incident_overview'] = incident_overview
                st.session_state.step = 3
            st.rerun()

    elif st.session_state.step == 3:
        st.header("Step 3: Estimated Compensation")
        with st.form(key='step3_form'):
            economic_damages = st.number_input("Economic Damages (e.g., Medical expenses, Lost wages, Property damage):", min_value=0.0, step=100.0, value=st.session_state.user_inputs.get('economic_damages', 0.0))
            non_economic_damages = st.number_input("Non-Economic Damages (e.g., Pain and suffering, Emotional distress):", min_value=0.0, step=100.0, value=st.session_state.user_inputs.get('non_economic_damages', 0.0))
            punitive_damages = st.number_input("Punitive Damages (if applicable):", min_value=0.0, step=100.0, value=st.session_state.user_inputs.get('punitive_damages', 0.0))
            submit_step3 = st.form_submit_button("Next")

        if submit_step3:
            st.session_state.user_inputs['economic_damages'] = economic_damages
            st.session_state.user_inputs['non_economic_damages'] = non_economic_damages
            st.session_state.user_inputs['punitive_damages'] = punitive_damages
            st.session_state.step = 4
            st.rerun()

    elif st.session_state.step == 4:
        st.header("Step 4: Upload Supporting Documents and Photos")
        with st.form(key='step4_form'):
            documents = st.file_uploader("Upload Documents (e.g., PDFs, DOCX)", type=["pdf", "docx"], accept_multiple_files=True)
            photos = st.file_uploader("Upload Photos (e.g., JPG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            submit_step4 = st.form_submit_button("Upload")

        if submit_step4:
            user_id = st.session_state.user_inputs.get('user_id')
            if documents:
                for doc in documents:
                    file_id = store_file_in_mongodb(doc, user_id, db)
                    st.success(f"Document {doc.name} uploaded successfully with ID {file_id}")
            if photos:
                for photo in photos:
                    file_id = store_file_in_mongodb(photo, user_id, db)
                    st.success(f"Photo {photo.name} uploaded successfully with ID {file_id}")
            st.session_state.user_inputs['documents'] = documents
            st.session_state.user_inputs['photos'] = photos
            st.session_state.step = 5
            st.rerun()

    elif st.session_state.step == 5:
        st.header("Step 5: Generate Comprehensive Report")
        if st.button("Generate Report"):
            with st.spinner('Searching for Arizona laws and medical literature...'):
                incident_overview = st.session_state.user_inputs.get('incident_overview')
                arizona_laws = fetch_arizona_laws(incident_overview)
                medical_literature = fetch_medical_literature(incident_overview)

            with st.spinner('Generating report...'):
                html_report = generate_report_with_openai(st.session_state.user_inputs, arizona_laws, medical_literature)

                if html_report:
                    st.success("Report generated successfully!")
                    user_id = st.session_state.user_inputs.get('user_id')
                    report_id = store_report_in_mongodb(html_report, user_id, db)
                    st.success(f"Report stored successfully with ID {report_id}")

                    st.write(html_report, unsafe_allow_html=True)
                    st.download_button("Download Report", data=html_report, file_name=f"legal_report_{datetime.now().strftime('%Y%m%d')}.html", mime="text/html")
            st.session_state.step = 6
            st.rerun()
    elif st.session_state.step == 6:
        st.header("Retrieve and Display Reports")
        user_id = st.text_input("Enter User ID to retrieve reports", value=st.session_state.user_inputs.get('user_id', ''))
        if st.button("Retrieve Reports"):
            reports = get_reports_by_user_id(user_id, db)
            if reports:

                for report in reports:
                    st.write(f"Report ID: {report['_id']}, Created At: {datetime.fromtimestamp(report['created_at'])}")
                    
                    # Display the HTML report
                    st.write(report["report_html"], unsafe_allow_html=True)

                    # Provide download button for the PDF
                    st.download_button(
                        label="Download",
                        data=report["report_html"],
                        file_name=f"report_{report['_id']}.html",
                        mime="text/html"
                    )
                  
            else:
                st.warning("No reports found for the given User ID.")

    
if __name__ == "__main__":
    main()
