FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends g++ make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY Makefile main.py demo.py ./
COPY src ./src
COPY tests ./tests
RUN make -j4 OPT=-O3 && make test OPT=-O3
CMD ["python3", "demo.py"]
