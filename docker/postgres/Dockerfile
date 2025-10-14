FROM postgis/postgis:17-3.5

RUN localedef -i fi_FI -c -f UTF-8 -A /usr/share/locale/locale.alias fi_FI.UTF-8

ENV LANG fi_FI.UTF-8

COPY ./init-extensions.sh /docker-entrypoint-initdb.d/init-extensions.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-extensions.sh
