FROM python:slim

RUN apt update && \
    apt install -y build-essential # rustc # XXX git

# RUN pip install transformers sentencepiece protobuf torch scipy # accelerate

# I hate this trend of dragging unversioned code from the Internet straight into
# a build. Guys, it is not 1998 anymore. Versioning is a thing. Package
# management is a solved problem.

# XXX RUN pip install -i https://pypi.org/simple/ bitsandbytes
# XXX RUN pip install git+https://github.com/huggingface/accelerate

# XXX to avoid build times, collapse into RUN above....
RUN pip install transformers
RUN pip install sentencepiece
RUN pip install protobuf
RUN pip install torch
RUN pip install scipy
# RUN pip install
# RUN pip install -q  sentencepiece accelerate==0.21.0 peft==0.4.0 bitsandbytes==0.40.2 transformers==4.31.0 trl==0.4.7 tensorboard

COPY ulizallama.py /app/

CMD /usr/local/bin/python /app/ulizallama.py

