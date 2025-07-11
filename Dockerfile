FROM python:3.13

RUN apt-get update && apt-get install -y git

WORKDIR /app 

RUN git clone https://github.com/even-more-effective/ea-forum-mcp-server.git

RUN pip install --no-cache-dir -r ea-forum-mcp-server/requirements.txt

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
]
CMD /bin/sh -c "cd /app/ea-forum-mcp-server && python -m src.httpServer & cd /app && exec chainlit run --host 0.0.0.0 --port 8080 app.py"
