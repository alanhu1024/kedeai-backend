FROM agentaai/templates:main

ARG ROOT_PATH=/
ENV ROOT_PATH=${ROOT_PATH}

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt
RUN chmod u+rwx entrypoint.sh

EXPOSE 80

CMD ["/app/entrypoint.sh"]
# uvicorn agenta_backend.main:app --reload --host 0.0.0.0 --port 8881