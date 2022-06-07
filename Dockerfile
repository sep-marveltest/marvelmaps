FROM python:3.8

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

ADD assets /Users/sephuls/Desktop/MarvelMapsApp/assets
ADD data /Users/sephuls/Desktop/MarvelMapsApp/data
ADD data.py /Users/sephuls/Desktop/MarvelMapsApp/data.py
ADD plots.py /Users/sephuls/Desktop/MarvelMapsApp/plots.py
ADD utils.py /Users/sephuls/Desktop/MarvelMapsApp/utils.py

# Install production dependencies.
RUN pip install -r requirements.txt

EXPOSE 8080

CMD python app.py