from dataclasses import dataclass
from urllib.parse import urlencode
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
    """Временная заглушка для будущей интеграции с платежным API."""

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        invoice_id = f'stub-invoice-{user_id}-{amount_rub}'
        return Invoice(invoice_id=invoice_id, pay_url=f'https://example.com/pay/{invoice_id}')

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        return PaymentStatus(invoice_id=invoice_id, state='pending')


class CryptoBotProvider:
    """Интеграция с @CryptoBot через Crypto Pay API."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.base_url = 'https://pay.crypt.bot/api'

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        url = f"{self.base_url}/createInvoice"
        
        headers = {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json"
        }
        
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
                    error_text = await resp.text()
                    raise RuntimeError(f"CryptoBot API error: {resp.status} - {error_text}")
                
                response_data = await resp.json()
        
        if not response_data.get('ok'):
            raise RuntimeError(f"CryptoBot invoice creation failed: {response_data}")
        
        result = response_data['result']
        
        # Используем правильное поле для URL
        pay_url = result.get('bot_invoice_url') or result.get('pay_url')
        
        return Invoice(invoice_id=str(result['invoice_id']), pay_url=pay_url)

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        url = f"{self.base_url}/getInvoices"
        
        headers = {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json"
        }
        
        # Для GET запроса с параметрами
        params = {'invoice_ids': invoice_id}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=20) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"CryptoBot API error: {resp.status} - {error_text}")
                
                data = await resp.json()
        
        if not data.get('ok'):
            raise RuntimeError(f"CryptoBot getInvoices failed: {data}")
        
        items = data.get('result', {}).get('items', [])
        if not items:
            return PaymentStatus(invoice_id=invoice_id, state='not_found')
        
        # Статус может быть 'active', 'paid', 'expired'
        status = items[0].get('status', 'pending')
        return PaymentStatus(invoice_id=invoice_id, state=status)


class DonationAlertsProvider:
    """Интеграция с DonationAlerts для приема донатов."""

    def __init__(self, token: str, base_url: str) -> None:
        self.token = token
        self.base_url = base_url.rstrip('/')

    async def create_invoice(self, user_id: int, amount_rub: int, payload: str | None = None) -> Invoice:
        # Создаем уникальный ID инвойса
        timestamp = int(time.time())
        invoice_id = payload or f"donation_{user_id}_{amount_rub}_{timestamp}"
        
        # Параметры для DonationAlerts
        params = {
            'amount': amount_rub,
            'currency': 'RUB',
            'comment': f'VPN subscription for user {user_id}',
            'payload': invoice_id,
            'token': self.token  # Добавляем токен для авторизации
        }
        
        # Формируем URL для доната
        # Для DonationAlerts используется формат: https://www.donationalerts.com/r/username
        pay_url = f"{self.base_url}?{urlencode(params)}"
        
        return Invoice(invoice_id=invoice_id, pay_url=pay_url)

    async def get_status(self, invoice_id: str) -> PaymentStatus:
        # Для DonationAlerts нужно настроить webhook
        # Пока возвращаем pending
        return PaymentStatus(invoice_id=invoice_id, state='pending')


# Фабрика для создания провайдера
def get_payment_provider(provider_name: str, settings):
    """Создает платежный провайдер на основе настроек"""
    print(f"DEBUG: Creating payment provider for: {provider_name}")
    print(f"DEBUG: Settings type: {type(settings)}")
    print(f"DEBUG: Settings dir: {dir(settings)}")
    
    if provider_name == "cryptobot":
        token = getattr(settings, 'cryptobot_api_token', None)
        print(f"DEBUG: CryptoBot token exists: {bool(token)}")
        if not token:
            raise ValueError("CryptoBot API token not configured")
        return CryptoBotProvider(token=token)
    
    elif provider_name == "donationalerts":
        token = getattr(settings, 'donationalerts_token', None)
        base_url = getattr(settings, 'donationalerts_base_url', None)
        
        print(f"DEBUG: DonationAlerts token exists: {bool(token)}")
        print(f"DEBUG: DonationAlerts base_url: {base_url}")
        
        if not token:
            raise ValueError("DonationAlerts token not configured")
        
        # Если base_url не задан, используем значение по умолчанию
        if not base_url:
            base_url = "https://www.donationalerts.com/r/countvpn"
            print(f"DEBUG: Using default base_url: {base_url}")
            
        return DonationAlertsProvider(
            token=token,
            base_url=base_url
        )
    
    else:
        print(f"DEBUG: Using stub provider for: {provider_name}")
        return StubPaymentProvider()