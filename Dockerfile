FROM python:3.7
ARG MODE
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
WORKDIR /code/app
ADD ./app /code/app
ADD ./utils /code/utils/
ADD ./assets /code/assets
COPY requirements.txt /code
COPY .env /code
RUN pip install --upgrade pip
RUN pip install -r ../requirements.txt
CMD /code/utils/docker/web/docker-web-dev.sh
