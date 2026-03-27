from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
import hmac
from urllib.parse import urlencode
import json
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
import logging
=======
>>>>>>> main
import time

import aiohttp


<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
logger = logging.getLogger(__name__)


=======
>>>>>>> main
@dataclass(slots=True)
class PaymentStatus:
    invoice_id: str
    state: str


@dataclass(slots=True)
class Invoice:
    invoice_id: str
    pay_url: str


class StubPaymentProvider:
    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        invoice_id = payload or f"stub-invoice-{user_id}-{amount_rub}"
        return Invoice(invoice_id=invoice_id, pay_url=f"https://example.com/pay/{invoice_id}")

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        return PaymentStatus(invoice_id=invoice_id, state='pending')


class RedirectPaymentProvider:
    def __init__(self, base_url: str, provider_name: str) -> None:
        self.base_url = base_url.rstrip('/')
        self.provider_name = provider_name

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        invoice_id = payload or f"{self.provider_name}_{user_id}_{amount_rub}_{int(time.time())}"
        query = urlencode({'amount': amount_rub, 'payload': invoice_id})
        return Invoice(invoice_id=invoice_id, pay_url=f"{self.base_url}?{query}")

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        return PaymentStatus(invoice_id=invoice_id, state='pending')


class FreekassaProvider:
    def __init__(self, merchant_id: str, secret_word_1: str) -> None:
        self.merchant_id = merchant_id
        self.secret_word_1 = secret_word_1
        self.base_url = 'https://pay.fk.money/'

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        order_id = payload or f"fk_{user_id}_{int(time.time())}"
        amount = f"{amount_rub:.2f}"
        currency = 'RUB'
        sign = md5(f"{self.merchant_id}:{amount}:{self.secret_word_1}:{currency}:{order_id}".encode()).hexdigest()
        params = {
            'm': self.merchant_id,
            'oa': amount,
            'currency': currency,
            'o': order_id,
            's': sign,
            'lang': 'ru',
        }
        return Invoice(invoice_id=order_id, pay_url=f"{self.base_url}?{urlencode(params)}")

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        return PaymentStatus(invoice_id=invoice_id, state='pending')


class SeverPayProvider:
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
    def __init__(self, base_url: str, mid: int, token: str, sign_delimiter: str = '|') -> None:
        self.base_url = base_url.rstrip('/')
        self.mid = mid
        self.token = token
        self.sign_delimiter = sign_delimiter
        logger.info("SeverPayProvider initialized. base_url=%s mid=%s", self.base_url, self.mid)

    def _generate_sign(self, data: dict) -> str:
        sorted_data = dict(sorted(data.items()))
        sign_payload = self.sign_delimiter.join(str(v) for v in sorted_data.values())
        sign = hmac.new(self.token.encode(), sign_payload.encode(), digestmod='sha256').hexdigest()
        logger.debug("SeverPay sign generated. payload=%s delimiter=%s", sign_payload, self.sign_delimiter)
        return sign

    def _build_payload(self, data: dict) -> dict:
=======
    def __init__(self, base_url: str, mid: int, token: str) -> None:
        self.base_url = base_url.rstrip('/')
        self.mid = mid
        self.token = token

    def _sign_payload(self, data: dict) -> dict:
>>>>>>> main
        payload = dict(data)
        payload['mid'] = self.mid
        payload['salt'] = f"{int(time.time())}-{payload.get('order_id', 'order')}"
        payload_sorted = dict(sorted(payload.items()))
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
        payload_sorted['sign'] = self._generate_sign(payload_sorted)
=======
        payload_sorted['sign'] = hmac.new(
            self.token.encode(),
            json.dumps(payload_sorted, ensure_ascii=False).encode(),
            digestmod='sha256',
        ).hexdigest()
>>>>>>> main
        return payload_sorted

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        order_id = payload or f"sp_{user_id}_{int(time.time())}"
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
        request_data = self._build_payload(
=======
        request_data = self._sign_payload(
>>>>>>> main
            {
                'order_id': order_id,
                'amount': float(amount_rub),
                'currency': 'RUB',
                'client_id': str(user_id),
                'client_email': f"user{user_id}@example.com",
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
                'email': f"user{user_id}@example.com",
            }
        )
        logger.info("Creating SeverPay invoice. order_id=%s amount=%s", order_id, amount_rub)
=======
            }
        )
>>>>>>> main
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/payin/create",
                json=request_data,
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
                timeout=30,
            ) as resp:
                raw_text = await resp.text()
                logger.debug("SeverPay /payin/create response status=%s body=%s", resp.status, raw_text)
                try:
                    data = json.loads(raw_text)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"SeverPay invalid JSON response: {raw_text}") from e
                if resp.status != 200:
                    raise RuntimeError(f"SeverPay HTTP {resp.status}: {data}")
                if not data.get('status'):
=======
                timeout=20,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or not data.get('status'):
>>>>>>> main
                    raise RuntimeError(f"SeverPay create payment error: {data}")
        return Invoice(invoice_id=str(data['data']['id']), pay_url=data['data']['url'])

    async def get_status(self, invoice_id: str) -> PaymentStatus:
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
        status_map = {
            'new': 'pending',
            'process': 'pending',
            'success': 'paid',
            'decline': 'failed',
            'fail': 'failed',
        }
        request_data = self._build_payload({'id': str(invoice_id)})
        logger.info("Fetching SeverPay status. invoice_id=%s", invoice_id)
=======
        request_data = self._sign_payload({'id': str(invoice_id)})
>>>>>>> main
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/payin/get",
                json=request_data,
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
                timeout=30,
            ) as resp:
                raw_text = await resp.text()
                logger.debug("SeverPay /payin/get response status=%s body=%s", resp.status, raw_text)
                if resp.status != 200:
                    logger.error("SeverPay status HTTP error: %s body=%s", resp.status, raw_text)
                    return PaymentStatus(invoice_id=invoice_id, state='pending')
                try:
                    data = json.loads(raw_text)
                except json.JSONDecodeError:
                    logger.error("SeverPay status invalid JSON: %s", raw_text)
                    return PaymentStatus(invoice_id=invoice_id, state='pending')
                if not data.get('status'):
                    logger.error("SeverPay status payload error: %s", data)
                    return PaymentStatus(invoice_id=invoice_id, state='pending')
        upstream_state = str(data.get('data', {}).get('status', 'new'))
        return PaymentStatus(invoice_id=invoice_id, state=status_map.get(upstream_state, 'pending'))
=======
                timeout=20,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or not data.get('status'):
                    return PaymentStatus(invoice_id=invoice_id, state='pending')
        return PaymentStatus(invoice_id=invoice_id, state=str(data.get('data', {}).get('status', 'pending')))
>>>>>>> main


class CryptoBotProvider:
    def __init__(self, token: str) -> None:
        self.token = token
        self.base_url = 'https://pay.crypt.bot/api'

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        url = f"{self.base_url}/createInvoice"
        headers = {"Crypto-Pay-API-Token": self.token, "Content-Type": "application/json"}
        data = {
            "currency_type": "fiat",
            "fiat": "RUB",
            "amount": str(amount_rub),
            "description": f"VPN subscription for user {user_id}",
            "allow_comments": False,
            "allow_anonymous": False,
        }
        if payload:
            data["payload"] = payload
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=20) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"CryptoBot API error: {resp.status} - {await resp.text()}")
                response_data = await resp.json()
        if not response_data.get('ok'):
            raise RuntimeError(f"CryptoBot invoice creation failed: {response_data}")
        result = response_data['result']
        pay_url = result.get('bot_invoice_url') or result.get('pay_url')
        return Invoice(invoice_id=str(result['invoice_id']), pay_url=pay_url)

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        url = f"{self.base_url}/getInvoices"
        headers = {"Crypto-Pay-API-Token": self.token, "Content-Type": "application/json"}
        params = {'invoice_ids': invoice_id}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=20) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"CryptoBot API error: {resp.status} - {await resp.text()}")
                data = await resp.json()
        if not data.get('ok'):
            raise RuntimeError(f"CryptoBot getInvoices failed: {data}")
        items = data.get('result', {}).get('items', [])
        if not items:
            return PaymentStatus(invoice_id=invoice_id, state='not_found')
        return PaymentStatus(invoice_id=invoice_id, state=items[0].get('status', 'pending'))


<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
class DonationAlertsProvider:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        webhook_secret: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.webhook_secret = webhook_secret

    def _oauth_token(self) -> str | None:
        return self.access_token or self.token

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        invoice_id = payload or f"da_{user_id}_{amount_rub}_{int(time.time())}"
        params = {
            'amount': amount_rub,
            'currency': 'RUB',
            'comment': f'VPN subscription for user {user_id}',
            'payload': invoice_id,
        }
        oauth_token = self._oauth_token()
        if oauth_token:
            params['token'] = oauth_token
        return Invoice(invoice_id=invoice_id, pay_url=f"{self.base_url}?{urlencode(params)}")

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        # Для DonationAlerts статус обычно подтверждается вебхуком.
        return PaymentStatus(invoice_id=invoice_id, state='pending')

    def verify_webhook(self, signature: str | None) -> bool:
        if not self.webhook_secret:
            return True
        return bool(signature and hmac.compare_digest(signature, self.webhook_secret))


def get_payment_provider(provider_name: str, settings):
    provider = provider_name.lower()
    logger.info("Creating payment provider: %s", provider)
=======
def get_payment_provider(provider_name: str, settings):
    provider = provider_name.lower()
>>>>>>> main

    if provider == "cryptobot":
        if not settings.cryptobot_token:
            raise ValueError("CryptoBot token not configured")
        return CryptoBotProvider(settings.cryptobot_token)

    if provider == "freekassa":
        if not settings.freekassa_shop_id or not settings.freekassa_secret_word_1:
            raise ValueError("FreeKassa credentials not configured")
        return FreekassaProvider(settings.freekassa_shop_id, settings.freekassa_secret_word_1)

    if provider == "severpay":
        if not settings.severpay_mid or not settings.severpay_token:
            raise ValueError("SeverPay credentials not configured")
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
        return SeverPayProvider(
            settings.severpay_base_url,
            settings.severpay_mid,
            settings.severpay_token,
            sign_delimiter=settings.severpay_sign_delimiter,
        )
=======
        return SeverPayProvider(settings.severpay_base_url, settings.severpay_mid, settings.severpay_token)
>>>>>>> main

    if provider == "cryptocloud":
        if not settings.cryptocloud_api_key:
            raise ValueError("CryptoCloud API key not configured")
        return RedirectPaymentProvider("https://cryptocloud.plus", provider)

    if provider == "donationalerts":
        if not settings.donationalerts_base_url:
            raise ValueError("DonationAlerts url not configured")
<<<<<<< codex/remove-secrets-and-add-payment-gateways-o59w8t
        return DonationAlertsProvider(
            base_url=settings.donationalerts_base_url,
            token=settings.donationalerts_token,
            access_token=settings.donationalerts_access_token,
            refresh_token=settings.donationalerts_refresh_token,
            client_id=settings.donationalerts_client_id,
            client_secret=settings.donationalerts_client_secret,
            webhook_secret=settings.donationalerts_webhook_secret,
        )
=======
        return RedirectPaymentProvider(settings.donationalerts_base_url, provider)
>>>>>>> main

    if provider == "boosty":
        if not settings.boosty_base_url:
            raise ValueError("Boosty url not configured")
        return RedirectPaymentProvider(settings.boosty_base_url, provider)

    if provider == "crystalpay":
        if not settings.crystalpay_base_url:
            raise ValueError("CrystalPay url not configured")
        return RedirectPaymentProvider(settings.crystalpay_base_url, provider)

    if provider == "platega":
        if not settings.platega_base_url:
            raise ValueError("Platega url not configured")
        return RedirectPaymentProvider(settings.platega_base_url, provider)

    return StubPaymentProvider()
