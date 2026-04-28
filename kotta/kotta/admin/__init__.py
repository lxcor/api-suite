"""Register all kotta models with Django admin."""

from kotta.admin.endpoint import EndpointAdmin
from kotta.admin.tier import TierAdmin, TierEndpointLimitInline
from kotta.admin.user_tier import UserTierAdmin
from kotta.admin.usage_counter import UsageCounterAdmin

__all__ = [
    'EndpointAdmin',
    'TierAdmin',
    'TierEndpointLimitInline',
    'UserTierAdmin',
    'UsageCounterAdmin',
]
