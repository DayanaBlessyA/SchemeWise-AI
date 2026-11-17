# SchemeWise AI

**AI-powered Government Scheme Discovery and Eligibility Assistant**

SchemeWise AI helps users discover Indian government schemes that may match their personal details and requirements.

## Features

- Collects user details such as age, gender, state, caste, annual family income and purpose.
- Matches user profiles against a government schemes dataset.
- Uses AI to provide scheme explanations.
- Displays scheme benefits, eligibility details and official website links.
- Includes support for Female, Male, Transgender Person and Other gender options.

## Technologies Used

- Python
- FastAPI
- HTML, CSS and JavaScript
- Google Gemini API
- Pandas
- CSV dataset

## Project Structure

```text
SchemeWise-AI/
├── data/
│   └── Schemes.csv
├── services/
│   ├── eligibility.py
│   └── gemini_service.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── main.py
├── requirements.txt
└── README.md
```

## Run Locally

1. Install Python.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

4. Start the application:

```bash
uvicorn main:app --reload
```

5. Open `http://127.0.0.1:8000` in your browser.

## Important Note

Scheme matches are potential matches, not confirmation of eligibility. Users should verify the latest eligibility criteria and application details on the respective official government websites.

## Project Track

Homingo Hack Days – LLM Apps