FROM python:3

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY requirements_installer.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_installer.txt
# Workaround to get right dotenv
RUN pip install -U python-dotenv

COPY ./maillist.py ./maillist.py
COPY ./installer.py ./installer.py

# Run mailist as daemon, reduce logs to avoid flooding the disk.
CMD [ "python", "./mail_list.py", "-d", "-r" ]
