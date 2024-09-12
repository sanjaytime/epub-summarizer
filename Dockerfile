FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY summarize.py .
COPY run_summarizer.sh .

RUN chmod +x run_summarizer.sh

CMD ["/bin/bash"]
