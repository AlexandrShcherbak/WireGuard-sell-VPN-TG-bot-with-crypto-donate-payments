from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
import hmac
from urllib.parse import urlencode
import json
import time

import aiohttp


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
    def __init__(self, base_url: str, mid: int, token: str) -> None:
        self.base_url = base_url.rstrip('/')
        self.mid = mid
        self.token = token

    def _sign_payload(self, data: dict) -> dict:
        payload = dict(data)
        payload['mid'] = self.mid
        payload['salt'] = f"{int(time.time())}-{payload.get('order_id', 'order')}"
        payload_sorted = dict(sorted(payload.items()))
        payload_sorted['sign'] = hmac.new(
            self.token.encode(),
            json.dumps(payload_sorted, ensure_ascii=False).encode(),
            digestmod='sha256',
        ).hexdigest()
        return payload_sorted

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        order_id = payload or f"sp_{user_id}_{int(time.time())}"
        request_data = self._sign_payload(
            {
                'order_id': order_id,
                'amount': float(amount_rub),
                'currency': 'RUB',
                'client_id': str(user_id),
                'client_email': f"user{user_id}@example.com",
            }
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/payin/create",
                json=request_data,
                timeout=20,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or not data.get('status'):
                    raise RuntimeError(f"SeverPay create payment error: {data}")
        return Invoice(invoice_id=str(data['data']['id']), pay_url=data['data']['url'])

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        request_data = self._sign_payload({'id': str(invoice_id)})
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/payin/get",
                json=request_data,
                timeout=20,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or not data.get('status'):
                    return PaymentStatus(invoice_id=invoice_id, state='pending')
        return PaymentStatus(invoice_id=invoice_id, state=str(data.get('data', {}).get('status', 'pending')))


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


def get_payment_provider(provider_name: str, settings):
    provider = provider_name.lower()

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
        return SeverPayProvider(settings.severpay_base_url, settings.severpay_mid, settings.severpay_token)

    if provider == "cryptocloud":
        if not settings.cryptocloud_api_key:
            raise ValueError("CryptoCloud API key not configured")
        return RedirectPaymentProvider("https://cryptocloud.plus", provider)

    if provider == "donationalerts":
        if not settings.donationalerts_base_url:
            raise ValueError("DonationAlerts url not configured")
        return RedirectPaymentProvider(settings.donationalerts_base_url, provider)

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
