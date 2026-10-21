from app.agents.graph import build_graph
from app.integrations.email.local_provider import InMemoryEmailProvider
from app.integrations.tasks.local_provider import InMemoryTaskProvider


def test_graph_can_compile_without_client_data():
    graph = build_graph(
        InMemoryEmailProvider(),
        InMemoryTaskProvider(),
    )
    assert graph is not None
