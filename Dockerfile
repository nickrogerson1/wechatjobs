FROM python:3.12

ENV PYTHONUNBUFFERED=1

# If you don't need any system packages from apt, you can remove this entirely
# or leave it if you want to install something else.
# RUN apt-get update && apt-get install -y

# --no-install-recommends \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# This CMD removes both Celery and parallel usage, 
# only doing your Django migrations followed by Gunicorn.
CMD sh -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn jobsite.wsgi"