FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run mailist as daemon, reduce logs to avoid flooding the disk.
CMD [ "python", "./mail_list.py", "-d", "-r" ]
