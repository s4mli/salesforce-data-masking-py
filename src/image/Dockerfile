FROM python:3.8-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 80
ENV region ap-southeast-2
CMD ["python3", "./process.py"]
