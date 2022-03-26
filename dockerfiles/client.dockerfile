FROM node:14-alpine
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY client/package.json  /usr/src/app
COPY client/package-lock.json /usr/src/app/
RUN npm install
COPY client/ /usr/src/app
