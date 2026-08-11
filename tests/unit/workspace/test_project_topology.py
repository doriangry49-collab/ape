"""
Unit tests for ProjectTopology Graph (PR-W2).
"""


from ape.workspace.project import ProjectTopology


def test_project_topology_topological_sort():
    topo = ProjectTopology("ECommerce App")

    topo.add_project("Backend API", "backend", "/services/backend")
    topo.add_project("Frontend Web", "frontend", "/web", dependencies=["Backend API"])
    topo.add_project("Mobile App", "mobile", "/mobile", dependencies=["Backend API"])

    order = topo.get_topological_order()
    names = [node.name for node in order]

    assert names[0] == "Backend API"
    assert "Frontend Web" in names[1:]
    assert "Mobile App" in names[1:]
