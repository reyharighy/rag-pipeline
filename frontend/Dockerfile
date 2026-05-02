FROM node:20-slim AS base

WORKDIR /app

RUN chown -R node:node /app

USER node

COPY --chown=node:node package.json package-lock.json ./

RUN npm install

COPY --chown=node:node . .

FROM base AS development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]