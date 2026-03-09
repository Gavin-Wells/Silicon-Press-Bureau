FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3847

# 启动时安装依赖，确保挂载 volume 后 node_modules 完整（含 i18next 等）
CMD ["sh", "-c", "npm install && npm run dev -- --host"]
