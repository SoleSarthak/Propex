from setuptools import setup, find_packages

setup(
    name="dep-mapper-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "confluent-kafka>=2.3.0",
        "neo4j>=5.18.0",
        "redis>=5.0.0",
        "httpx>=0.27.0",
    ],
)
