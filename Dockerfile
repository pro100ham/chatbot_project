FROM ollama/ollama:latest

RUN apt-get update && apt-get install -y \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

ENTRYPOINT ["/bin/bash"]
CMD ["/startup.sh"]