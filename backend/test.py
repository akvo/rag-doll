import pika
import json
import os

def send_test_message_to_queue(text):
    pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
    pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                                int(os.getenv("RABBITMQ_PORT")),
                                                '/', pika_credentials)
    connection = pika.BlockingConnection(pika_parameters)
    channel = connection.channel()

    test_message = {
        'to': {
            'phone': '+6281999103535',
        },
        'text': f'Hi Galih from {text}, You can login into APP_NAME by click this link: http://localhost:3001/verify/123456'
    }

    channel.basic_publish(exchange='', routing_key=os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES"), body=json.dumps(test_message))
    connection.close()

send_test_message_to_queue("""
                           Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at vehicula felis, at eleifend lectus. Mauris cursus lobortis neque pellentesque aliquam. Suspendisse vitae justo lorem. In cursus nulla sapien, vel blandit turpis egestas gravida. Aenean ac fermentum elit. In vel neque convallis, iaculis eros vel, semper mauris. Integer tincidunt posuere tincidunt. Donec auctor elit sed lacinia condimentum. Maecenas congue consectetur lorem eu bibendum.

Pellentesque tempus gravida magna at lacinia. Duis gravida tortor et pretium tincidunt. Mauris quis facilisis magna. Suspendisse nec metus ornare, faucibus arcu sit amet, gravida augue. Phasellus tincidunt nulla ac orci fermentum, quis lacinia ligula ullamcorper. Nulla facilisis vulputate congue. Sed sit amet congue lectus. Vivamus elementum commodo lacus vitae ultricies. Nunc aliquam quis diam quis egestas. Cras porttitor, felis et ultricies dapibus, ex tellus mattis metus, condimentum egestas ligula sem eget ante. Cras mauris ex, molestie in dictum ut, vestibulum eget eros.

Fusce molestie fermentum tortor, cursus scelerisque ipsum aliquet ut. Maecenas tempor dui eu mauris pulvinar commodo. Curabitur enim est, suscipit eget felis non, eleifend malesuada ante. Vivamus in eleifend leo. Donec accumsan porttitor magna, ut euismod ligula. Morbi nibh mauris, tincidunt nec ligula quis, pretium malesuada magna. Phasellus lacinia aliquam enim, id hendrerit lorem luctus iaculis.
                           """)