import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession


class SignalListener:
    def __init__(self, api_id, api_hash, session_string, channels,
                 signal_regex, on_signal):
        if session_string:
            self.client = TelegramClient(
                StringSession(session_string), api_id, api_hash
            )
        else:
            self.client = TelegramClient("autobet_session", api_id, api_hash)
        
        self.channels = channels
        self.signal_regex = re.compile(
            signal_regex, re.IGNORECASE | re.DOTALL
        )
        self.on_signal = on_signal
        self.last_signal = None

    def parse_signal(self, text):
        if not text:
            return None
        m = self.signal_regex.search(text)
        if not m:
            return None
        return {
            "period": m.group(1).strip(),
            "prediction": m.group(2).upper(),
            "amount": int(m.group(3).replace(",", "")),
            "bot_step": int(m.group(4)),
            "raw": text,
        }

    async def start(self):
        await self.client.start()
        print("✅ Telegram connected", flush=True)
        print(f"👂 Listening to {len(self.channels)} channel(s)...", flush=True)

        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            text = event.message.text or ""
            print(f"📩 Message received", flush=True)
            signal = self.parse_signal(text)
            if not signal:
                return
            key = (signal["period"], signal["prediction"])
            if self.last_signal == key:
                print(f"⚠️ Duplicate: {key}", flush=True)
                return
            self.last_signal = key
            print(f"🎯 {signal['prediction']} | P{signal['period']} | "
                  f"{signal['amount']:,} | Step {signal['bot_step']}x", flush=True)
            try:
                await self.on_signal(signal)
            except Exception as e:
                print(f"❌ Callback error: {e}", flush=True)

        await self.client.run_until_disconnected()
