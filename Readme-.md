# AI-Legal Report Generator
This project is a web-based AI-Legal Report Generator built using Streamlit, MongoDB, and OpenAI's GPT-4. The application allows users to upload documents and images, input case details, fetch relevant laws and medical literature, and generate detailed legal reports. These reports are stored in a MongoDB database for future retrieval and downloading.

## Table of Contents
- Features
- Installation
- Usage
- Technologies Used
- MongoDB Integration
- OpenAI Integration
- File Upload and Processing
- PDF Generation and Download
- File Storage and Retrieval

## Features
- Client Data Collection: Users can input case information including client details, incident date, and estimated compensation.
- Document and Image Upload: Upload supporting documents (PDF/DOCX) and photos (JPG/PNG).
- OpenAI GPT-4 Integration: Generate comprehensive legal reports using OpenAI's GPT-4, combining case details with fetched Arizona laws and medical literature.
- PDF and HTML Report Generation: Generate and store HTML reports, with an option to download the report in PDF format.
- MongoDB Integration: Store uploaded files and generated reports in a MongoDB database, with metadata including user ID, file type, and upload timestamp.
- Download Reports: Retrieve previously generated reports from the database and download them in HTML format.

## Installation
Prerequisites
Python 3.8 or higher
MongoDB installed locally or MongoDB Atlas
OpenAI API key
Install Required Packages
Clone this repository:

```
git clone https://github.com/your-repository/ai-legal-report-generator.git
cd ai-legal-report-generator
```
Install the required Python packages:

```
pip install -r requirements.txt
```
Set Up OpenAI API Key
To use the OpenAI GPT-4 model, set your OpenAI API key as an environment variable:

```
export OPENAI_API_KEY='your_openai_api_key'
```
Or set it in your .env file:

```
OPENAI_API_KEY=your_openai_api_key
```
### Set Up MongoDB
Ensure MongoDB is running locally, or connect to a MongoDB Atlas instance. By default, the app uses mongodb://localhost:27017/ as the connection string.

To change this, edit the get_mongo_client function in main.py:


client = MongoClient("your_mongodb_connection_string")
## Usage
Run the Streamlit app:

```
streamlit run main.py
```
Open your browser and navigate to:

```
http://localhost:8501
```
Follow the steps in the app to input client information, upload documents, generate a legal report, and download the report in PDF or HTML format.

## Technologies Used
- Streamlit: For building the web interface.
- MongoDB: For storing user data, files, and generated reports.
- OpenAI GPT-4: For generating legal reports based on case data.
- Textract & Tesseract: For text extraction from uploaded documents and images.

### MongoDB Integration

The app connects to a local MongoDB instance to store:

- Uploaded files (PDFs, DOCX, and images) in binary format.
- Generated legal reports in HTML format.
- Key MongoDB Functions
- store_file_in_mongodb(file, user_id, db): Stores uploaded files in the database.
- store_report_in_mongodb(report_html, user_id, db): Stores generated reports in the database.
get_reports_by_user_id(user_id, db): Retrieves all reports for a given user.

### OpenAI Integration
The app uses OpenAI's GPT-4 to generate legal reports. The following steps are performed:

- Collect user inputs (client name, incident overview, compensation details).
- Fetch relevant Arizona laws and medical literature using Google Scholar and Google Search APIs.
- Send a detailed prompt to OpenAI to generate a comprehensive legal report in HTML format.

### File Upload and Processing
- Textract is used to process uploaded files (PDFs and DOCX) and extract text content.

- Uploaded files are stored in MongoDB in binary format for easy retrieval.

### Users can:

- View the report in HTML format directly in the app.
- Download the report as an HTML file or a PDF.
### File Storage and Retrieval
- Files and reports are stored in MongoDB with metadata including user_id, file_type, and created_at timestamps.
- Users can retrieve their reports by entering their user_id and download previously generated reports.