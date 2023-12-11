# LLMBrowser :computer:

This is a Python-based web task automation tool. It uses Selenium and GPT-4V (Other vision LLMs coming soon!) to automate tasks in a web browser. :robot:

![System Diagram](https://i.imgur.com/PDuB8VL.png)

## Getting Started :rocket:

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites :clipboard:

You need to have Python installed on your machine. You can download it from [here](https://www.python.org/downloads/).

You also need to install the required Python packages. You can do this by running the following command in your terminal:

```sh
pip install -r requirements.txt
```

### Environment Variables :earth_americas:

This project uses environment variables for configuration. Copy the `.env.example` file to a new file named `.env` and fill in the appropriate values.

```sh
cp .env.example .env
```

### Installing :wrench:

To get a development environment running, follow these steps:

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Install the required packages.
4. Set up the environment variables.
5. Run the main script:

```sh
python llm.py
```

## Usage :computer:

The main script will prompt you to enter a task. The task should be a goal that you want to achieve on a website. The script will then generate the necessary Selenium code to achieve this goal.

## License :page_with_curl:

This project is licensed under the MIT License - see the [`LICENSE`](command:_github.copilot.openRelativePath?%5B%22LICENSE%22%5D "LICENSE") file for details.

## Contact :mailbox:

If you have any questions, feel free to open an issue or submit a pull request. We love contributions from the community! :heart:
