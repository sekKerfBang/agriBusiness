import stripe
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    """Service de paiement Stripe"""
    
    @staticmethod
    def create_payment_intent(amount, currency='eur', metadata=None):
        """
        Crée un PaymentIntent Stripe
        amount: en euros (ex: 29.99)
        """
        try:
            # Convertir en centimes
            amount_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            logger.info(f"PaymentIntent créé: {payment_intent.id}")
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            raise
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """Récupère un PaymentIntent"""
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération PaymentIntent: {e}")
            raise
    
    @staticmethod
    def create_refund(payment_intent_id, amount=None):
        """Crée un remboursement"""
        try:
            params = {'payment_intent': payment_intent_id}
            if amount:
                params['amount'] = int(amount * 100)  # En centimes
            
            refund = stripe.Refund.create(**params)
            logger.info(f"Remboursement créé: {refund.id}")
            return refund
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur remboursement: {e}")
            raise
    
    @staticmethod
    def validate_webhook(payload, sig_header, endpoint_secret):
        """Valide un webhook Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature invalide: {e}")
            return None