"""
Lottery API Client - Login + GetResults + PlaceBet
"""
import time
import secrets
import requests


class LotteryClient:
    def __init__(self, username, password, base_url, origin):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.origin = origin
        
        self.token = None
        self.token_header = "Bearer "
        self.sign = None
        self.expires_at = 0
        self.user_info = {}
        
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-MM,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "ar-origin": origin,
            "content-type": "application/json;charset=UTF-8",
            "origin": origin,
            "referer": origin + "/",
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Mobile Safari/537.36"
            ),
        })
    
    # ==========================================
    # 🔐 LOGIN
    # ==========================================
    def login(self):
        """Login ပြီး token + sign ယူ"""
        try:
            payload = {
                "username": self.username,
                "pwd": self.password,
                "phonetype": 1,
                "logintype": "mobile",
                "packId": "",
                "deviceId": secrets.token_hex(16),
                "pixelId": "",
                "fbcId": "",
                "fbc": "",
                "fbp": "",
                "adId": "",
                "language": 7,
                "random": secrets.token_hex(16),
                "signature": "",
                "timestamp": int(time.time()),
            }
            
            res = self.session.post(
                f"{self.base_url}/api/webapi/Login",
                json=payload,
                timeout=15
            )
            data = res.json()
            
            if data.get("code") != 0:
                print(f"❌ Login failed: {data.get('msg')}", flush=True)
                return False
            
            d = data["data"]
            self.token = d["token"]
            self.token_header = d.get("tokenHeader", "Bearer ")
            self.expires_at = int(d.get("expiresIn", 0))
            
            self.session.headers["authorization"] = f"{self.token_header}{self.token}"
            
            print(f"✅ Login success", flush=True)
            print(f"   Expires at: {self.expires_at}", flush=True)
            
            # userInfo ယူ (sign အတွက်)
            return self._fetch_user_info()
        
        except Exception as e:
            print(f"❌ Login error: {e}", flush=True)
            return False
    
    def _fetch_user_info(self):
        """userInfo (sign ပါ) ယူ"""
        try:
            res = self.session.post(
                f"{self.base_url}/api/webapi/GetUserInfo",
                json={"language": 7},
                timeout=10
            )
            data = res.json()
            if data.get("code") == 0:
                self.user_info = data.get("data", {})
                self.sign = self.user_info.get("sign")
                print(f"✅ Sign: {self.sign[:20]}..." if self.sign else "⚠️ No sign", flush=True)
                return True
            print(f"⚠️ GetUserInfo failed: {data.get('msg')}", flush=True)
            return False
        except Exception as e:
            print(f"❌ GetUserInfo error: {e}", flush=True)
            return False
    
    # ==========================================
    # 💰 BALANCE
    # ==========================================
    def get_balance(self):
        """လက်ကျန်စစ်"""
        try:
            res = self.session.post(
                f"{self.base_url}/api/webapi/GetBalance",
                json={},
                timeout=10
            )
            data = res.json()
            if data.get("code") == 0:
                return float(data.get("data", {}).get("amount", 0))
        except Exception:
            pass
        return None
    
    # ==========================================
    # 📊 LATEST PERIOD
    # ==========================================
    def get_latest_period(self):
        """API က နောက်ဆုံး period ယူ (prefix အတွက်)"""
        try:
            payload = {
                "pageSize": 10,
                "pageNo": 1,
                "typeId": 30,
                "language": 7,
                "random": secrets.token_hex(16),
                "signature": "",
                "timestamp": int(time.time()),
            }
            res = self.session.post(
                f"{self.base_url}/api/webapi/GetNoaverageEmerdList",
                json=payload,
                timeout=10
            )
            data = res.json()
            if data.get("code") == 0:
                lst = data.get("data", {}).get("list", [])
                if lst:
                    return str(lst[0].get("issueNumber"))
        except Exception as e:
            print(f"❌ GetLatestPeriod error: {e}", flush=True)
        return None
    
    # ==========================================
    # 🎯 PLACE BET
    # ==========================================
    def place_bet(self, period, prediction, amount):
        """
        Bet ထိုး
        
        Args:
            period: "20260919100051911" (full)
            prediction: "BIG" or "SMALL"
            amount: int
        
        Returns:
            dict: {"code": int, "msg": str, "raw": dict}
        """
        select_type = 13 if prediction.upper() == "BIG" else 14
        
        payload = {
            "typeId": 30,
            "issuenumber": str(period),
            "amount": int(amount),
            "betCount": 1,
            "gameType": 2,
            "selectType": select_type,
            "language": 7,
            "random": secrets.token_hex(16),
            "signature": self.sign,
            "timestamp": int(time.time()),
        }
        
        try:
            res = self.session.post(
                f"{self.base_url}/api/webapi/GameBetting",
                json=payload,
                timeout=15
            )
            data = res.json()
            return {
                "code": data.get("code"),
                "msg": data.get("msg", ""),
                "raw": data,
            }
        except Exception as e:
            return {"code": -1, "msg": str(e), "raw": {}}
    
    # ==========================================
    # 🔄 TOKEN CHECK
    # ==========================================
    def needs_refresh(self):
        """Token expire ဖို့ ၅ မိနစ် အောက် ရှိလား"""
        if not self.expires_at:
            return True
        return (self.expires_at - time.time()) < 300
