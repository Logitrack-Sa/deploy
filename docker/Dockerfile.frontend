FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8080
ARG NEXT_PUBLIC_BASE_PATH=
ARG NEXT_PUBLIC_COURIER_STATUS_MODEL=legacy
ARG NEXT_PUBLIC_CUSTOMER_CANCELLATION_ENABLED=false
ENV NEXT_PUBLIC_API_GATEWAY_URL=$NEXT_PUBLIC_API_GATEWAY_URL \
    NEXT_PUBLIC_BASE_PATH=$NEXT_PUBLIC_BASE_PATH \
    NEXT_PUBLIC_COURIER_STATUS_MODEL=$NEXT_PUBLIC_COURIER_STATUS_MODEL \
    NEXT_PUBLIC_CUSTOMER_CANCELLATION_ENABLED=$NEXT_PUBLIC_CUSTOMER_CANCELLATION_ENABLED
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN mkdir -p public && npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S -g 1001 nextjs && adduser -S -u 1001 -G nextjs nextjs \
    && rm -rf /usr/local/lib/node_modules/npm /opt/yarn-*
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /app/public ./public
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000'+(process.env.APP_BASE_PATH||'')+'/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
