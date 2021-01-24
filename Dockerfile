FROM python:3

COPY . /demucs_service
WORKDIR /demucs_service
RUN pip install -r requirements.txt 
EXPOSE 5000
ENTRYPOINT [ "python" ] 
CMD [ "server.py"] 