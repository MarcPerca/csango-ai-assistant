FROM python:3.11-slim

WORKDIR /app
COPY . .

ENV HOST=0.0.0.0
ENV PORT=7860
EXPOSE 7860

CMD ["python", "server.py"]
