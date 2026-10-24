FROM mageai/mageai:latest@sha256:440970d14b6e1c66e879650c35564cf5125cbbed56032c0fb8337808fdf012fe

USER root

# Install Microsoft's driver in the Mage runtime (host installation is separate).
# https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg unixodbc unixodbc-dev build-essential libgssapi-krb5-2 \
    && if ! odbcinst -q -d -n 'ODBC Driver 18 for SQL Server' >/dev/null 2>&1; then \
         . /etc/os-release; \
         curl -fsSL "https://packages.microsoft.com/config/${ID}/${VERSION_ID}/packages-microsoft-prod.deb" -o /tmp/packages-microsoft-prod.deb \
         && dpkg -i /tmp/packages-microsoft-prod.deb \
         && apt-get update \
         && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
         && rm /tmp/packages-microsoft-prod.deb; \
       fi \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# The upstream image runs as root; it does not guarantee a user named "mage".
