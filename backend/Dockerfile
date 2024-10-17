FROM python:3.9

# Install locales package and other necessary tools
RUN apt-get update && apt-get install -y locales locales-all

# Generate and set the nl_NL.UTF-8 locale
RUN sed -i '/nl_NL.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen nl_NL.UTF-8 && \
    update-locale LANG=nl_NL.UTF-8 LC_ALL=nl_NL.UTF-8

# Set the locale environment variables
ENV LANG nl_NL.UTF-8
ENV LANGUAGE nl_NL:nl
ENV LC_ALL nl_NL.UTF-8

# RUN apt-get update && \
#     apt-get install -y \
#         locales && \
#     rm -r /var/lib/apt/lists/*

# RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
#     sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
#     dpkg-reconfigure --frontend=noninteractive locales

# ENV LANG nl_NL.UTF-8
# ENV LANGUAGE nl_NL:nl
# ENV LC_ALL nl_NL.UTF-8    

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
