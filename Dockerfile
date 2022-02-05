FROM ghcr.io/missemily2022/mirbot:ultra

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

RUN apt-get -qq install -y p7zip-full p7zip-rar aria2 curl pv jq ffmpeg locales python3-lxml

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]
