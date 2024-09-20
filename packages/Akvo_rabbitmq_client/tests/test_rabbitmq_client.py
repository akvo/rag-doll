import pytest
from unittest.mock import AsyncMock, patch
from Akvo_rabbitmq_client import rabbitmq_client


@pytest.mark.asyncio
@patch("aio_pika.connect", new_callable=AsyncMock)
async def test_producer_and_consumer(mock_connect):
    # Mocking connection and channel
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    mock_queue = AsyncMock()

    mock_connect.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel
    mock_channel.declare_exchange.return_value = mock_exchange
    mock_channel.declare_queue.return_value = mock_queue

    # Mocking message consume and publish
    callback_mock = AsyncMock()

    await rabbitmq_client.initialize()
    await rabbitmq_client.consume(
        queue_name="test_queue",
        routing_key="test_queue",
        callback=callback_mock,
    )
    await rabbitmq_client.producer(
        body="Test producer and consumer", routing_key="test_queue"
    )

    # Simulate message delivery to the consumer
    incoming_message_mock = AsyncMock()
    incoming_message_mock.body.decode.return_value = (
        "Test producer and consumer"
    )
    await rabbitmq_client.consumer_callback(
        message=incoming_message_mock,
        routing_key="test_queue",
        callback=callback_mock,
    )

    callback_mock.assert_called_once_with(body="Test producer and consumer")


@pytest.mark.asyncio
@patch("aio_pika.connect", new_callable=AsyncMock)
async def test_connection_error(mock_connect):
    # Simulate connection failure
    mock_connect.side_effect = ConnectionError("Failed to connect to RabbitMQ")

    with pytest.raises(ConnectionError):
        await rabbitmq_client.initialize()
