"""
Bet Engine - Signal → Bet ထိုး
"""
import time


class BetEngine:
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.last_period_bet = None
        self.stats = {
            "total": 0,
            "success": 0,
            "skip": 0,
            "fail": 0,
        }
    
    # ==========================================
    # 🎯 MAIN
    # ==========================================
    def process_signal(self, signal):
        """Signal ကို လက်ခံပြီး bet ထိုး"""
        self.stats["total"] += 1
        
        period_short = signal["period"]
        prediction = signal["prediction"]
        amount = signal["amount"]
        bot_step = signal["bot_step"]
        
        print(f"\n━━━ Processing Signal ━━━", flush=True)
        print(f"Period: {period_short} | {prediction} | {amount:,} | Step {bot_step}x", flush=True)
        
        # === 1. Bot Step စစ် ===
        if bot_step >= 3:
            self.stats["skip"] += 1
            print(f"⏭️ Skip - Bot Step {bot_step}x (3x+)", flush=True)
            return
        
        # === 2. Amount စစ် ===
        if amount < self.config["MIN_BET"]:
            self.stats["skip"] += 1
            print(f"⏭️ Skip - Amount {amount} < Min {self.config['MIN_BET']}", flush=True)
            return
        
        if amount > self.config["MAX_BET"]:
            self.stats["skip"] += 1
            print(f"⏭️ Skip - Amount {amount} > Max {self.config['MAX_BET']}", flush=True)
            return
        
        # === 3. Token စစ် ===
        if self.client.needs_refresh():
            print("🔄 Token refresh needed, re-login...", flush=True)
            if not self.client.login():
                self.stats["fail"] += 1
                print("❌ Re-login failed", flush=True)
                return
        
        # === 4. Balance စစ် ===
        balance = self.client.get_balance()
        if balance is not None and balance < amount:
            self.stats["skip"] += 1
            print(f"⏭️ Skip - Balance {balance:.0f} < Bet {amount}", flush=True)
            return
        
        # === 5. Full Period ဖန်တီး ===
        full_period = self._resolve_period(period_short)
        if not full_period:
            self.stats["fail"] += 1
            print(f"❌ Cannot resolve period {period_short}", flush=True)
            return
        
        print(f"🔗 Full Period: {full_period}", flush=True)
        
        # === 6. Duplicate check ===
        if self.last_period_bet == full_period:
            self.stats["skip"] += 1
            print(f"⏭️ Skip - Already bet {full_period}", flush=True)
            return
        
        # === 7. DRY RUN ===
        if self.config["DRY_RUN"]:
            self.stats["success"] += 1
            self.last_period_bet = full_period
            print(f"🧪 [DRY RUN] Bet {amount:,} on {prediction} @ {full_period}", flush=True)
            print(f"📊 Stats: {self.stats}", flush=True)
            return
        
        # === 8. BET ထိုး ===
        result = self.client.place_bet(full_period, prediction, amount)
        
        if result["code"] == 0:
            self.stats["success"] += 1
            self.last_period_bet = full_period
            print(f"✅ Bet Success!", flush=True)
            print(f"   Period: {full_period}", flush=True)
            print(f"   {prediction} | {amount:,}", flush=True)
            if balance:
                print(f"   Balance: {balance:,.0f}", flush=True)
        
        elif "signature" in result["msg"].lower():
            self.stats["fail"] += 1
            print(f"⚠️ Wrong signature, refreshing...", flush=True)
            self.client._fetch_user_info()
            # Retry once
            result2 = self.client.place_bet(full_period, prediction, amount)
            if result2["code"] == 0:
                self.stats["success"] += 1
                self.last_period_bet = full_period
                print(f"✅ Bet Success (retry) @ {full_period}", flush=True)
            else:
                print(f"❌ Bet failed: {result2['msg']}", flush=True)
        
        elif "period" in result["msg"].lower() or "clos" in result["msg"].lower():
            self.stats["skip"] += 1
            print(f"⏭️ Period closed (signal နောက်ကျ): {full_period}", flush=True)
        
        elif "balance" in result["msg"].lower():
            self.stats["skip"] += 1
            print(f"⏭️ Balance low", flush=True)
        
        else:
            self.stats["fail"] += 1
            print(f"❌ Bet failed: {result['msg']}", flush=True)
        
        print(f"📊 Stats: {self.stats}", flush=True)
    
    # ==========================================
    # 🔗 PERIOD RESOLVE
    # ==========================================
    def _resolve_period(self, short_period):
        """
        Signal ရဲ့ '911' ကို
        API ရဲ့ prefix နဲ့ ပေါင်းပြီး full period ဖန်တီး
        """
        latest = self.client.get_latest_period()
        if not latest:
            print("⚠️ Cannot get latest period", flush=True)
            return None
        
        print(f"📊 Latest period: {latest}", flush=True)
        
        # Prefix = latest ရဲ့ နောက်ဆုံး ၃ လုံး ဖယ်
        prefix = latest[:-3]
        full = prefix + short_period
        return full
