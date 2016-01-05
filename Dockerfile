FROM library/celery

USER root


RUN apt-get update && apt-get install -y git curl g++ make libmagic1 imagemagick libjpeg-dev libtiff-dev libpng-dev
RUN pip install --upgrade pip

RUN curl -O http://www.leptonica.com/source/leptonica-1.72.tar.gz
RUN tar xf leptonica-1.72.tar.gz 
RUN cd leptonica-1.72; ./configure && make -j`nproc` && make install; cd ..
RUN curl -O https://tesseract-ocr.googlecode.com/files/tesseract-ocr-3.02.02.tar.gz
RUN tar xf tesseract-ocr-3.02.02.tar.gz
RUN cd tesseract-ocr/; ./configure && make -j`nproc` && make install; cd ..
RUN ldconfig

ADD webocr webocr
ADD webocr/webocr/tasks.py /data/tasks.py
ADD run.sh /usr/local/bin/run.sh

RUN pip install -r webocr/requirements.txt
RUN pip install -e webocr

RUN curl -O https://tesseract-ocr.googlecode.com/files/tesseract-ocr-3.02.eng.tar.gz
RUN tar xf tesseract-ocr-3.02.eng.tar.gz

USER user

ENV TESSDATA_PREFIX /home/user/tesseract-ocr
ENV C_FORCE_ROOT 1

CMD ["/bin/bash", "/usr/local/bin/run.sh"]
