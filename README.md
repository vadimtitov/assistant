# Assistant
A highly customizable virtual assistant that has several interfaces including voice, chatbot and web api.

# Install
``` git clone https://github.com/vadimtitov/assistant.git
cd assistant
bash install
``` 
 * Was only tested on Raspbian and Linux Mint so far.
# Set up google cloud platform project for speech-to-text
Create Google CLoud Platform project and download your credentials following [these instructions](https://cloud.google.com/docs/authentication/getting-started). 
Copy your project id to `GOOGLE_PROJECT_ID` variable inside `assistant/custom/credentials/set_env_var`. 
Place your credentials file into `assistant/custom/credentials/` and specify path to it in `GOOGLE_APPLICATION_CREDENTIALS` variable inside `assistant/custom/credentials/set_env_var`.
Then activate [Cloud Speech-To-Text API](https://console.developers.google.com/apis/library/speech.googleapis.com/) for your project.

# Set up AWS for text-to-speech
Create your [AWS](https://aws.amazon.com/) account, get `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` and insert them into `assistant/custom/credentials/set_env_var`. This ensures you can use Amazon Polly text-to-speech generator.

# Set up Telegram bot
1. Create a Telegram account if you don't have one yet
2. To find out your telegram account id send command `\my_id` to [this bot](https://t.me/get_id_bot). Once you have it insert it into `assistant/custom/telegram_config.py` file into `ALLOWED_USERS_DICT` under `admin` key. You can grant access to other users here as well.
3. To create new bot send command `/newbot` to [FatherBot](https://t.me/botfather) and follow the instructions
4. Copy bot token into `assistant/custom/telegram_config.py`
5. You can also specify custom bot keyboard in `assistant/custom/telegram_config.py`.

# Create custom hotword
You can train your assistant to respond to any name. For that use [Snowboy](https://snowboy.kitt.ai/) hotword detection service. Log in and click `Create Hotword`. After providing 3 audio samples download your model file `your_hotword.pmdl` and place it inside `assistant/custom/snowboy_models/`.

# Personalities 
Take a look inside `assistant/custom/snowboy_models/personalities.yaml`:
  - `calls_me`: specify how assitant will call you (e.g. your name)
  - `sensitivity`: sensitivity ∈ [0, 1] of your hotword , adjust this to find optimal response rate/false detection. Typically 0.3-0.5 works good.
  - `keyword_file`: `your_hotword.pmdl` from the step above
  - `responds_folder`: a folder located inside `assistant/custom/call_responds/` that contains mp3 files with pre-recorded assistant responces (e.g "yes?", "aha?", "how can I help?"). Pre-recording makes responds much faster. To generate these mp3 files use [Amazon Polly]((https://aws.amazon.com/polly/)). Click `Get Started with Amazon Polly` and log in to see all available voices.
  - `polly_voice`: a "name" of Amazon Polly voice of your choice. 



