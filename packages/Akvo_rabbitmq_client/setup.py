from setuptools import setup, find_packages

setup(
    name="Akvo_rabbitmq_client",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "aio-pika==9.4.2",
        "pytest==8.2.2",
        "pytest-asyncio==0.23.7",
    ],
    author="Akvo",
    author_email="tech.consultancy@akvo.org",
    description="A RabbitMQ client package for Rag Doll.",
    # url='https://github.com/yourusername/rabbitmq-client',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.5",
)
