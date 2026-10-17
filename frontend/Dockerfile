# Etapa 1: compilación
FROM node:20-alpine AS compilacion
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY . .
RUN npm run build

# Etapa 2: servicio con nginx (proxy /api -> backend)
FROM nginx:alpine
COPY --from=compilacion /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
