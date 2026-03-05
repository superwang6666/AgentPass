from setuptools import setup

setup(
    name="agentpass-client",
    version="1.0.0",
    description="AgentPass Client SDK - Agent-side implementation for machine-to-machine login",
    author="",
    license="MIT",
    py_modules=["agentpass_client"],
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.7",
)
