FROM lambci/lambda:build-python3.7

ENV REQPATH /root/requirements.txt
COPY ./requirements.txt /root/requirements.txt
RUN pip3 install -r ${REQPATH} --target=/opt/python/root/

COPY ./src/main.py /opt/python/root/main.py

RUN cd /opt/python/root && zip -r /lambda-layer.zip *