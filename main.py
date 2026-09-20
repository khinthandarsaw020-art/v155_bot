import asyncio
import sys
import os
from config import (
    TG_API_ID, TG_API_HASH, TG_SESSION_STRING, TG_CHANNEL_ID,
    SITE_USER, SITE_PASS, SITE_BASE_URL, SITE_ORIGIN,
    DRY_RUN, MIN_BET, MAX_BET, SIGNAL_REGEX,
)
from lottery_client import LotteryClient
from telegram_listener import SignalListener
from bet_engine import BetEngine


async def main():
    print("🚀 Auto Bet Bot Starting...", flush=True)
    print(f"   DRY_RUN = {DRY_RUN}", flush=True)

    if not TG_API_ID or not TG_API_HASH:
        print("❌ TG_API_ID/HASH မရှိ", flush=True)
        return
    if not SITE_USER or not SITE_PASS:
        print("❌ SITE_USER/PASS မရှိ", flush=True)
        return
    if not TG_CHANNEL_ID:
        print("❌ TG_CHANNEL_ID မရှိ", flush=True)
        return

    client = LotteryClient(SITE_USER, SITE_PASS, SITE_BASE_URL, SITE_ORIGIN)
    if not client.login():
        print("❌ Login failed", flush=True)
        return

    balance = client.get_balance()
    print(f"💰 Balance: {balance:,.2f}" if balance else "💰 Unknown", flush=True)

    engine = BetEngine(client, {
        "DRY_RUN": DRY_RUN,
        "MIN_BET": MIN_BET,
        "MAX_BET": MAX_BET,
    })

    async def on_signal(signal):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, engine.process_signal, signal)

    listener = SignalListener(
        api_id=TG_API_ID,
        api_hash=TG_API_HASH,
        session_string=TG_SESSION_STRING,
        channels=[TG_CHANNEL_ID],
        signal_regex=SIGNAL_REGEX,
        on_signal=on_signal,
    )

    print("👂 Listening...", flush=True)
    await listener.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Bye", flush=True)
