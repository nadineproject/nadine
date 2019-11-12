############################################################
# Dockerfile to run a Django-based web application
# Based on an Ubuntu Image
############################################################

# Set the base image to use to python 2.7
FROM python:3.7

# Set the file maintainer (your name - the file's author)
MAINTAINER Jacob Sayles

# Don't buffer stdout and stderr
ENV PYTHONUNBUFFERED 1

# Set env variables used in this Dockerfile (add a unique prefix, such as DOCKYARD)
# Local directory with project source
ENV DOCKYARD_SRC=./
# Directory in container for all project files
ENV DOCKYARD_SRVHOME=/webapp
# Directory in container for project source files
ENV DOCKYARD_SRVPROJ=/webapp/nadine

# Update the default application repository sources list
RUN apt-get update \
    && apt-get -y dist-upgrade \
    && apt-get install -y libjpeg-dev gunicorn postgresql-client
#RUN apt-get -y autoremove

# Configure Postgresql
#RUN apt-get install -y postgresql-9.4
#USER postgres
#RUN /etc/init.d/postgresql start \
#    && psql --command "CREATE USER pguser WITH SUPERUSER PASSWORD 'pguser';" \
#    && createdb -O pguser nadinedb
#RUN mkdir -p /var/run/postgresql && chown -R postgres /var/run/postgresql
#VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]
#CMD ["/usr/lib/postgresql/9.4/bin/postgres", "-D", "/var/lib/postgresql/9.4/main", "-c", "config_file=/etc/postgresql/9.4/main/postgresql.conf"]
#USER root

# Create application subdirectories
WORKDIR $DOCKYARD_SRVHOME
RUN mkdir media static logs
VOLUME ["$DOCKYARD_SRVHOME/media/", "$DOCKYARD_SRVHOME/logs/"]

# Copy application source code to SRCDIR
COPY $DOCKYARD_SRC $DOCKYARD_SRVPROJ

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r $DOCKYARD_SRVPROJ/requirements.txt

# Install the demo data
WORKDIR $DOCKYARD_SRVPROJ
COPY $DOCKYARD_SRC/demo/local_settings.py $DOCKYARD_SRVPROJ/nadine/
#RUN /etc/init.d/postgresql start \
#  && ./manage.py restore_backup demo/demo_database.tar

# Port to expose
EXPOSE 8000

# Copy entrypoint script into the image
ENTRYPOINT ["./docker-entrypoint.sh"]
