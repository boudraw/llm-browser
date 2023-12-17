from setuptools import setup, find_packages

setup(
    name='llm_browser',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'openai',
        'selenium',
        'selenium-wire',
        'webdriver-manager',
        'environs',
        'beautifulsoup4',
        'Pillow',
        'tiktoken',
    ],
)