from setuptools import setup

setup(
    name="gdrivepy",
    version="1.0",
    py_modules=["gdrivepy"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        gdrivepy=gdrivepy:main
    """,
)
