import asyncio
import pytest
import socketio

from core.socketio_config import SOCKETIO_PATH


@pytest.mark.asyncio
async def test_chat_simple(event_loop, backend_url: str) -> None:
    """A simple websocket test using the sio_client fixture"""

    sio_client = socketio.AsyncClient()
    future = asyncio.get_running_loop().create_future()

    @sio_client.on('chats')
    def on_message_received(data):
        print(f"Client received: {data}")
        # set the result
        future.set_result(data)

    message = {
        "phone": "+628123456789",
        "reply": "Yes, John Doe, How are you?"
    }
    await sio_client.connect(
        url=backend_url,
        socketio_path=SOCKETIO_PATH,
    )
    await sio_client.emit('chats', message)
    # wait for the result to be set (avoid waiting forever)
    await asyncio.wait_for(future, timeout=1.0)
    await sio_client.disconnect()
    assert future.result() == message
