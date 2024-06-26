import socketio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


sio_server = socketio.AsyncServer(async_mode='asgi')


sio_app = socketio.ASGIApp(
    socketio_server=sio_server,
    socketio_path="sockets"
)


@sio_server.on('connect')
async def sio_connect(sid, environ):
    """Track user connection"""
    logger.info('A user connected')


@sio_server.on('disconnect')
async def sio_disconnect(sid):
    """Track user disconnection"""
    logger.info('User disconnected')


@sio_server.on('chats')
async def chat_message(sid, msg):
    """Receive a chat message and send to all clients"""
    logger.info(f"Server received: {msg}")
    await sio_server.emit('chats', msg)
