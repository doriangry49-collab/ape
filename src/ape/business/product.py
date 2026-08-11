"""
Product Domain Model — ORION-104 Venture-Centric Product Factory Specification.
Defines Product as a first-class value-producing domain entity.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ProductStatus(str, Enum):
    """Lifecycle status of an external product venture."""
    IDEA = "IDEA"
    VALIDATION = "VALIDATION"
    PLANNING = "PLANNING"
    DEVELOPMENT = "DEVELOPMENT"
    LAUNCHED = "LAUNCHED"
    SCALING = "SCALING"


class ProductType(str, Enum):
    """Supported product venture categories."""
    SAAS = "SAAS"
    MEDIA_CHANNEL = "MEDIA_CHANNEL"
    ECOMMERCE = "ECOMMERCE"
    MOBILE_APP = "MOBILE_APP"
    CHROME_EXTENSION = "CHROME_EXTENSION"


@dataclass
class Product:
    """Primary value-producing product entity managed by APE Venture Engine."""
    product_id: str
    name: str
    product_type: ProductType = ProductType.SAAS
    status: ProductStatus = ProductStatus.IDEA
    owner_company: str = "APE Holding"
    revenue: float = 0.0
    cost: float = 0.0
    artifacts: List[str] = field(default_factory=list)
    deployments: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    @property
    def roi_percentage(self) -> float:
        """Calculate Return on Investment (ROI) percentage."""
        if self.cost <= 0.0:
            return 100.0 if self.revenue > 0.0 else 0.0
        return ((self.revenue - self.cost) / self.cost) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Product entity into dictionary payload."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "product_type": self.product_type.value,
            "status": self.status.value,
            "owner_company": self.owner_company,
            "revenue": self.revenue,
            "cost": self.cost,
            "roi_percentage": round(self.roi_percentage, 2),
            "artifacts_count": len(self.artifacts),
            "deployments_count": len(self.deployments),
        }
