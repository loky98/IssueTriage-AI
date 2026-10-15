from langchain_core.messages import AIMessage, HumanMessage

from app.agent import MAX_TOOL_ROUNDS, route_after_investigate


def ai_with_tool():
    return AIMessage(content="", tool_calls=[{"name": "get_issue", "args": {"number": 1}, "id": "1"}])


def test_goes_to_tools_when_requested():
    assert route_after_investigate({"messages": [HumanMessage("hi"), ai_with_tool()]}) == "tools"


def test_goes_to_draft_without_tool_calls():
    assert route_after_investigate({"messages": [HumanMessage("hi"), AIMessage("done")]}) == "draft"


def test_stops_after_max_rounds():
    msgs = [HumanMessage("hi")] + [ai_with_tool() for _ in range(MAX_TOOL_ROUNDS + 1)]
    assert route_after_investigate({"messages": msgs}) == "draft"