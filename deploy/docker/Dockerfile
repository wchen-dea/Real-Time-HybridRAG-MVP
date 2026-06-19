FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --no-cache-dir -e .
EXPOSE 8088
CMD ["uvicorn", "dataops_graphrag_mcp.app.api:app", "--host", "0.0.0.0", "--port", "8088"]
