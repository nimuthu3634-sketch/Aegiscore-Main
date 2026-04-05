FROM node:24-alpine

WORKDIR /srv/apps/web

COPY apps/web/package.json ./package.json
RUN npm install

COPY apps/web ./
COPY infra/docker/web-entrypoint.sh /usr/local/bin/web-entrypoint.sh
RUN chmod +x /usr/local/bin/web-entrypoint.sh

EXPOSE 5173

ENTRYPOINT ["web-entrypoint.sh"]
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
