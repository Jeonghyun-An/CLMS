# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --prefer-offline --no-audit --progress=false

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]