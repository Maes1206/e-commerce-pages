# FastAPI contact form

1. Install dependencies:
   `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set your SMTP values.
3. Run the API:
   `uvicorn main:app --reload`
4. Serve the HTML site and keep the contact forms pointing to:
   `http://127.0.0.1:8000/contact`

Health check:
`http://127.0.0.1:8000/healthz`
