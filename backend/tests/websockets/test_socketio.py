import asyncio
import pytest
import socketio
from unittest.mock import AsyncMock, patch

from core.socketio_config import SOCKETIO_PATH


@pytest.mark.asyncio
async def test_chat_simple() -> None:
    sio_client = socketio.AsyncClient(
        engineio_logger=True,
        logger=True,
    )
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

    # Mock connect and emit methods
    with patch.object(
        sio_client, 'connect', new=AsyncMock()
    ) as mock_connect, patch.object(
        sio_client, 'emit', new=AsyncMock()
    ) as mock_emit, patch.object(
        sio_client, 'disconnect', new=AsyncMock()
    ) as mock_disconnect:

        # Simulate server sending a message
        async def mock_emit_side_effect(event, data, *args, **kwargs):
            if event == 'chats':
                await asyncio.sleep(0.1)  # Simulate some delay
                on_message_received(data)

        mock_emit.side_effect = mock_emit_side_effect

        await sio_client.connect(
            url='http://mockserver',
            socketio_path=SOCKETIO_PATH,
        )
        await sio_client.emit('chats', message)
        # wait for the result to be set (avoid waiting forever)
        await asyncio.wait_for(future, timeout=1.0)
        await sio_client.disconnect()

        # Assertions
        mock_connect.assert_called_once_with(
            url='http://mockserver', socketio_path=SOCKETIO_PATH)
        mock_emit.assert_called_once_with('chats', message)
        mock_disconnect.assert_called_once()

        assert future.result() == message
