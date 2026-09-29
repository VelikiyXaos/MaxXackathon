#!/usr/bin/env bash

set -euo pipefail

log() { printf '%s | %-5s | %s\n' "$(date -u +%H:%M:%S)" "${1}" "${2}"; }
info() { log INFO "$*"; }
warn() { log WARN "$*"; }
fail() { log FATAL "$*"; exit 1; }

DB_WAIT_SECONDS="${DB_WAIT_SECONDS:-60}"

wait_for_db() {
    [ -n "${DATABASE_URL:-}" ] || return 0

    info "жду PostgreSQL (до ${DB_WAIT_SECONDS}с)"
    local deadline=$((SECONDS + DB_WAIT_SECONDS))
    while [ "$SECONDS" -lt "$deadline" ]; do
        if python -c "
import asyncio, os, sys
from sqlalchemy import text
from db.database import engine

async def probe() -> int:
    try:
        async with engine.connect() as connection:
            await connection.execute(text('SELECT 1'))
    except Exception:
        return 1
    finally:
        await engine.dispose()
    return 0

sys.exit(asyncio.run(probe()))
" 2>/dev/null; then
            info "PostgreSQL готов"
            return 0
        fi
        sleep 1
    done

    fail "PostgreSQL не ответил за ${DB_WAIT_SECONDS}с — проверьте сервис db"
}

run_migrations() {
    info "применяю миграции: alembic upgrade head"
    if ! python -m alembic upgrade head; then
        warn "alembic upgrade head не прошёл — возможно, база помечена"
        warn "чужой ревизией (например, собрана на другой ветке)."
        warn "Варианты: docker compose down -v && docker compose up -d"
        warn "или пометить текущую схему: python -m alembic stamp head"
        return 1
    fi
    info "миграции применены"
}

case "${1:-bot}" in
    migrate)
        wait_for_db
        run_migrations
        ;;
    seed)
        wait_for_db
        shift
        info "заполняю базу: python -m scripts $*"
        python -m scripts "$@"
        ;;
    bot)
        wait_for_db
        info "запускаю бота"
        exec python -m bot.main
        ;;
    shell)
        exec /bin/bash
        ;;
    *)
        exec "$@"
        ;;
esac
