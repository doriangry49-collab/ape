"""
Unit tests for ORION-104 Venture-Centric Product Factory & Business Model Packs.
Verifies Product domain object, Venture lifecycle execution, and Business Model Pack registry.
"""


from ape.business import Product, ProductStatus, ProductType, VentureEngine
from ape.marketplace.business_packs import BusinessModelPackRegistry


def test_product_domain_entity():
    product = Product(
        product_id="prod_001",
        name="AI CRM SaaS",
        product_type=ProductType.SAAS,
        cost=1000.0,
        revenue=3500.0,
    )

    assert product.product_id == "prod_001"
    assert product.status == ProductStatus.IDEA
    assert product.roi_percentage == 250.0
    d = product.to_dict()
    assert d["name"] == "AI CRM SaaS"
    assert d["roi_percentage"] == 250.0


def test_venture_lifecycle_engine():
    engine = VentureEngine(holding_company="Acme AI Ventures")
    product = engine.create_product("YouTube Tech Channel", product_type=ProductType.MEDIA_CHANNEL, initial_cost=500.0)

    assert product.owner_company == "Acme AI Ventures"

    res = engine.run_venture_pipeline(product.product_id, target_market="Tech Content")

    assert res.pipeline_status == "LAUNCHED"
    assert res.confidence_score > 90.0
    assert product.status == ProductStatus.LAUNCHED
    assert product.revenue == 1250.0  # 500 * 2.5
    assert product.roi_percentage == 150.0
    assert len(res.artifacts_created) == 3


def test_business_model_pack_registry():
    reg = BusinessModelPackRegistry()
    packs = reg.list_packs()

    assert len(packs) == 3
    pack_ids = [p.pack_id for p in packs]
    assert "pack_saas_startup" in pack_ids
    assert "pack_youtube_studio" in pack_ids
    assert "pack_real_estate" in pack_ids

    saas_pack = reg.get_pack("pack_saas_startup")
    assert saas_pack is not None
    assert "CEO" in saas_pack.included_roles
    assert "Coder" in saas_pack.included_roles
