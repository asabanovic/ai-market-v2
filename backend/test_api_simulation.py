#!/usr/bin/env python3
"""Simulate API call to test db_session passing."""

import asyncio
from agents.graph import graph
from agents.context import AgentContext
from agents.state import InputState


class MockDBSession:
    """Mock database session for testing."""
    def __repr__(self):
        return "<MockDBSession>"

    def execute(self, query):
        """Mock execute method."""
        print(f"✅ DB execute called with query: {str(query)[:100]}...")
        # Return mock result
        class MockResult:
            def fetchall(self):
                return []
        return MockResult()


async def test_with_db_session():
    """Test graph invocation with db_session."""
    print("\n" + "="*60)
    print("TEST: Graph with DB Session")
    print("="*60)

    # Create input
    input_state = InputState(query="čokolada")

    # Create context WITH db_session (like the API does)
    mock_session = MockDBSession()
    context = AgentContext(db_session=mock_session)

    print(f"\n📋 Context created:")
    print(f"   db_session: {context.db_session}")
    print(f"   chat_model: {context.chat_model}")

    try:
        # Invoke graph exactly like the API does
        result = await graph.ainvoke(
            input_state.__dict__,
            config={"configurable": context.__dict__}
        )

        print(f"\n✅ Graph executed successfully!")
        print(f"Intent: {result.get('intent')}")
        print(f"Results count: {len(result.get('results', []))}")

        if result.get('error'):
            print(f"⚠️  Error: {result.get('error')}")
            return False
        else:
            print("✅ No errors!")
            return True

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_with_db_session())
    exit(0 if success else 1)
