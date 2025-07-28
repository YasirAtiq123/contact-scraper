# Contact Info Scraper (Flask + OpenAI)

This is a Flask web application that extracts the most likely **phone numbers** and **email addresses** for a list of companies using OpenAI's GPT-4o. Users can either upload an Excel file or paste company names directly. The app processes the input asynchronously and generates both a results file and a log file.

## Features

- Upload `.xlsx` files or enter company names via text
- Asynchronous processing with OpenAI's GPT-4o
- Drag-and-drop file upload with real-time progress display
- Automatic download of results and logs
- AJAX-based form submission (no page reload)
- Stylish, responsive frontend with toast notifications and loading spinner
- Filetype validation and drag-over effects
- Downloadable output and log files
- Rate limiting and basic security practices

## How It Works

1. User uploads a `.xlsx` file or enters company names.
2. Backend sends each company name to OpenAI and parses the response.
3. Data is saved into the original Excel file and a separate CSV log.
4. Download links are shown after processing.

## Technologies Used

- **Flask** for the backend
- **AsyncOpenAI** for contacting GPT-4o
- **HTML, CSS, JavaScript** for the frontend
- **Pandas** for file manipulation
- **Flask-Limiter** (optional) for rate limiting
- **dotenv** for managing secrets

## Folder Structure
```filesystem
project/
│
├── static/
│   ├── styles.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── uploads/
│   └── (Generated Excel & log files)
│
├── main.py
├── requirements.txt
└── README.md
```
## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/contact-info-scraper.git
    cd contact-info-scraper
    ```
2. **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4. **Setup environmental varaibles**:
Create a `.env` file in the root directory:
    ```environment variables
    OPENAI_API_KEY=<your_openai_api_key>
    ```
5. **Run the server**:
    ```bash
    python main.py
    ```
6. **Visit the app:**
Open `http://localhost:5000` in your browser.