FROM python:3

COPY . /demucs_service
WORKDIR /demucs_service
RUN apt update
RUN apt install -y ffmpeg
RUN pip install -r requirements.txt 
EXPOSE 5000
ENTRYPOINT [ "python" ] 
CMD [ "server.py"] 