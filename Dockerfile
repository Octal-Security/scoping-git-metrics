FROM python:3.11-slim

RUN apt update && apt install git -y

# install custom multimetric fork
RUN git clone https://github.com/adeadfed/multimetric /tmp/multimetric
WORKDIR /tmp/multimetric
RUN python /tmp/multimetric/setup.py install

# install app code
COPY ./app /app
WORKDIR /app
RUN pip install -r requirements.txt

RUN chmod +x /app/git_askpass.py
RUN chmod +x /app/analyze_repositories.py

ENTRYPOINT [ "/app/analyze_repositories.py" ]