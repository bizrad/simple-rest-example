FROM python:3.10-slim AS build-env
WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY app.py /app/app.py
RUN pip install -r requirements.txt && chmod +x /app/app.py
RUN black --check app.py
RUN pylint --fail-under 5 app.py
EXPOSE 8080
#ENTRYPOINT [ "/app/app.py" ]

FROM gcr.io/distroless/python3-debian11
COPY --from=build-env /app /app
COPY --from=build-env /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
WORKDIR /app
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages
CMD ["/app/app.py"]
