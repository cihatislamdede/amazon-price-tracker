# Amazon Price Tracker Discord Bot

A Discord bot that tracks the price of a product on Amazon and notifies the user when the price drops below a certain threshold.

## Installation

1. Clone the repository.
2. Install the required dependencies using the following command:

    ```shell
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory of the project and add the following environment variables:

    ```shell
    BOT_TOKEN=<your-bot-token>
    CHANNEL_ID=<discord-channel-id-for-notifications>
    ```

    > **Note:** You can get your bot token from [here](https://discord.com/developers/applications).

## Usage

1. Run the main Python file using the following command:

    ```shell
    python bot.py
    ```
