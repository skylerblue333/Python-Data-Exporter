FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --system --uid 10001 --create-home app
COPY main.py ./
COPY src ./src
USER 10001:10001
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
