FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel

WORKDIR /workspace

COPY . /workspace

RUN python setup.py install

EXPOSE 8888

CMD ["python", "server.py"]