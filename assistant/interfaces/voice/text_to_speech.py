import boto3,os

REGION_NAME = 'eu-west-2'


class TTS(object):

    def __init__(self,
        rootkey_file='assistant/custom/credentials/rootkey_polly.csv',
        audio_folder="assistant/custom/"
    ):
        self.audio_folder = audio_folder
        with open(rootkey_file) as file:
            keys = file.read().split('\n')
        keys = [key.split('=')[1] for key in keys]
        self.client = boto3.Session(
            aws_access_key_id=keys[0],
            aws_secret_access_key=keys[1],
            region_name=REGION_NAME).client('polly')

    def say(self, text, voiceID='Brian'):
        response = self.client.synthesize_speech(
            VoiceId=voiceID,
            OutputFormat='mp3',
            Text = text)
        with open(self.audio_folder + 'speech.mp3', 'wb') as file:
            file.write(response['AudioStream'].read())
        os.system(f'mpg123 {self.audio_folder}speech.mp3 >/dev/null 2>&1')
        os.system(f'rm {self.audio_folder}speech.mp3')

    def save_to_file(self, text, voiceID='Brian', name = ''):
        response = self.client.synthesize_speech(
            VoiceId=voiceID,
            OutputFormat='mp3',
            Text = text
        )
        name = name + '_' + '_'.join(text.split(' ')[0:4])
        with open(self.audio_folder + f'{name}.mp3', 'wb') as file:
            file.write(response['AudioStream'].read())

    def synthesize_speech(self, text):
        response = self.client.synthesize_speech(
            VoiceId='Brian',  #'Matthew'
            OutputFormat='ogg_vorbis',
            Text = text)
        return response['AudioStream'].read()
