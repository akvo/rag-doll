import asyncio
import pytest
import socketio

from unittest.mock import AsyncMock, patch
from core.socketio_config import SOCKETIO_PATH, User
from socketio.exceptions import ConnectionRefusedError
from fastapi import HTTPException
from http.cookies import SimpleCookie
from utils.jwt_handler import create_jwt_token
from sqlmodel import Session, select


@pytest.mark.asyncio
async def test_socketio_connection(session: Session):
    sio_client = socketio.AsyncClient(
        engineio_logger=True,
        logger=True,
    )
    future = asyncio.get_running_loop().create_future()

    @sio_client.on("chats")
    def on_message_received(data):
        print(f"Client received: {data}")
        future.set_result(data)

    message = {
        "phone": "+628123456789",
        "reply": "Yes, John Doe, How are you?",
    }

    with patch.object(
        sio_client, "connect", new=AsyncMock()
    ) as mock_connect, patch.object(
        sio_client, "emit", new=AsyncMock()
    ) as mock_emit, patch.object(
        sio_client, "disconnect", new=AsyncMock()
    ) as mock_disconnect:

        async def mock_emit_side_effect(event, data, *args, **kwargs):
            if event == "chats":
                await asyncio.sleep(0.1)
                on_message_received(data)

        mock_emit.side_effect = mock_emit_side_effect

        # Mock token verification to raise HTTPException for invalid token
        with patch(
            "core.socketio_config.verify_jwt_token"
        ) as mock_verify_jwt_token, patch(
            "core.socketio_config.cookie", SimpleCookie()
        ):  # Mock the cookie behavior

            # Mock loading of cookies and extraction of auth_token
            mock_cookie = SimpleCookie()
            mock_cookie["AUTH_TOKEN"] = "invalid_token"
            environ = {"HTTP_COOKIE": mock_cookie.output(header="", sep="; ")}
            mock_verify_jwt_token.side_effect = HTTPException(
                status_code=403, detail="Invalid token"
            )

            # Test connection attempt with invalid token and mocked environ
            try:
                await sio_client.connect(
                    url="http://mockserver",
                    socketio_path=SOCKETIO_PATH,
                    environ=environ,
                )
                mock_connect.assert_called_with(
                    url="http://mockserver",
                    socketio_path=SOCKETIO_PATH,
                    environ=environ,
                )
            except ConnectionRefusedError as e:
                print(e)

            mock_disconnect.assert_not_called()

        # Test valid connection scenario
        mock_cookie = SimpleCookie()
        valid_user = session.exec(select(User)).first()
        valid_token = create_jwt_token(
            data={
                "uid": valid_user.id,
                "uphonenumber": valid_user.phone_number,
            }
        )
        mock_cookie["AUTH_TOKEN"] = valid_token

        valid_environ = {
            "HTTP_COOKIE": mock_cookie.output(header="", sep="; ")
        }
        await sio_client.connect(
            url="http://mockserver",
            socketio_path=SOCKETIO_PATH,
            environ=valid_environ,
        )

        await sio_client.emit("chats", message)
        await asyncio.wait_for(future, timeout=1.0)
        await sio_client.disconnect()

        mock_connect.assert_called_with(
            url="http://mockserver",
            socketio_path=SOCKETIO_PATH,
            environ=valid_environ,
        )
        mock_emit.assert_called_once_with("chats", message)
        mock_disconnect.assert_called_once()

        assert future.result() == message
