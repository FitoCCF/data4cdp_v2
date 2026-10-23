FROM python:3.10-slim

WORKDIR /app

# Las dependencias se instalan desde requirements.txt (versiones fijas) antes de copiar el código,
# así Docker reutiliza la capa en caché mientras no cambien.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

