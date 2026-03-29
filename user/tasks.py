import logging

from celery import shared_task
from django.db import transaction as db_transaction
from django.db.models import F, Sum

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def mark_transactions_inactive(self):
    """
    Marks transactions as inactive if repaid_amount >= transaction_amount
    """

    from user.models import Transactions  # avoid circular imports

    logger.info("Started marking transactions inactive")

    queryset = (
        Transactions.objects
        .filter(is_active=True)
        .annotate(total_repaid=Sum("repayments__amount"))
        .filter(total_repaid=F("amount"))
    )

    total = queryset.count()
    logger.info(f"Found {total} transactions eligible for inactivation")

    queryset.update(is_active=False)
