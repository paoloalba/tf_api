FROM nginx

EXPOSE 80
EXPOSE 443

# Install Supervisord
RUN apt-get update && apt-get install -y supervisor \
&& rm -rf /var/lib/apt/lists/*
# Custom Supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /app/permanentstorage

RUN rm /etc/nginx/nginx.conf
COPY default_nginx.conf /etc/nginx/nginx.conf

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

ADD ./ssl_certificates/ app/ssl_certificates/

# RUN mkdir -p /app/ssl
# COPY nginx-selfsigned.crt /app/ssl/nginx-selfsigned.crt
# COPY nginx-selfsigned.key /app/ssl/nginx-selfsigned.key

CMD ["/usr/bin/supervisord"]