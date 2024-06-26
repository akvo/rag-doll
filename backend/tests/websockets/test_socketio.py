import asyncio
import pytest
import socketio


@pytest.mark.asyncio
async def test_chat_simple(event_loop) -> None:
    """A simple websocket test using the sio_client fixture"""

    sio_client = socketio.AsyncClient()
    future = asyncio.get_running_loop().create_future()

    @sio_client.on('chats')
    def on_message_received(data):
        print(f"Client received: {data}")
        # set the result
        future.set_result(data)

    message = 'Hello World!'
    await sio_client.connect(
        url='http://backend:5000/api',
        socketio_path='sockets'
    )
    await sio_client.emit('chats', message)
    # wait for the result to be set (avoid waiting forever)
    await asyncio.wait_for(future, timeout=1.0)
    await sio_client.disconnect()
    assert future.result() == message
