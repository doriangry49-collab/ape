"""
Unit tests for ORION-106A First Revenue-Generating Departments & First Real Venture Product.
Verifies Research, Marketing, Publishing departments, landing page generation, live deployment, and $27.00 initial revenue tracking.
"""


from ape.business import (
    MarketingDepartment,
    PublishingDepartment,
    ResearchDepartment,
    VentureLaunchPipeline,
)


def test_research_department_execution():
    dept = ResearchDepartment()
    report = dept.execute_task("Research Real Estate Automation Market")

    assert report.status == "COMPLETED"
    assert "Market Pain Point Analyzed" in report.findings[0]
    assert report.metrics["confidence_score"] == 94.0 if hasattr(report, "metrics") else report.kpis_calculated["confidence_score"] == 94.0


def test_marketing_department_landing_page_generation():
    dept = MarketingDepartment()
    html = dept.generate_landing_page("Real Estate Automation Mini-SaaS", "Automate listings in 5 minutes.")

    assert "<h1>Real Estate Automation Mini-SaaS</h1>" in html
    assert "Get Started Now" in html

    report = dept.execute_task("Generate Landing Page Copy")
    assert report.status == "COMPLETED"
    assert "Landing Page HTML generated" in report.findings[0]


def test_publishing_department_deployment_and_revenue():
    dept = PublishingDepartment()
    report = dept.execute_task("Real Estate Automation Mini-SaaS")

    assert report.status == "COMPLETED"
    assert "LIVE PRODUCT DEPLOYED at:" in report.findings[0]
    assert "FIRST REAL REVENUE RECORDED: $27.00" in report.findings[1]
    assert report.kpis_calculated["initial_revenue"] == 27.0


def test_full_4_department_first_venture_launch():
    pipeline = VentureLaunchPipeline()
    packet = pipeline.launch_first_venture(
        product_name="Real Estate Automation Mini-SaaS",
        target_market="Real Estate Turkey",
    )

    assert packet.product_name == "Real Estate Automation Mini-SaaS"
    assert packet.deployment_url.startswith("https://launch.ape.dev/products/")
    assert "Get Started Now" in packet.landing_page_html
    assert packet.initial_revenue == 27.0
    assert len(packet.merkle_evidence_proof) == 64
    assert len(packet.department_reports) == 4
