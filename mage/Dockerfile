FROM mageai/mageai:latest

USER root

# pyodbc needs unixODBC headers. Install the Microsoft ODBC driver separately
# after reviewing its license and the official installation instructions.
RUN apt-get update \
    && apt-get install -y --no-install-recommends unixodbc unixodbc-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

USER mage
