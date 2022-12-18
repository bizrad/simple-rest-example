FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY app.py /app/app.py
RUN pip install -r requirements.txt && chmod +x /app/app.py
RUN black --check app.py
RUN pylint --fail-under 5 app.py
EXPOSE 8080
ENTRYPOINT [ "/app/app.py" ]
