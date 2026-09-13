FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY hia ./hia
COPY evals ./evals
COPY app.py ./app.py

EXPOSE 7860
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
