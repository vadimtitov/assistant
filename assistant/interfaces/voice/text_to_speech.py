import os
import boto3


class TTS:
    def __init__(
        self,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        audio_folder="assistant/custom/",
        region_name=os.environ["AWS_REGION_NAME"],
    ):
        self.audio_folder = audio_folder

        self.client = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        ).client("polly")

    def say(self, text, voiceID="Brian"):
        response = self.client.synthesize_speech(
            VoiceId=voiceID, OutputFormat="mp3", Text=text
        )

        with open(self.audio_folder + "speech.mp3", "wb") as file:
            file.write(response["AudioStream"].read())

        os.system(f"mpg123 {self.audio_folder}speech.mp3 >/dev/null 2>&1")
        os.system(f"rm {self.audio_folder}speech.mp3")

    def save_to_file(self, text, voiceID="Brian", name=""):
        response = self.client.synthesize_speech(
            VoiceId=voiceID, OutputFormat="mp3", Text=text
        )
        name = name + "_" + "_".join(text.split(" ")[0:4])
        with open(self.audio_folder + f"{name}.mp3", "wb") as file:
            file.write(response["AudioStream"].read())

    def synthesize_speech(self, text):
        response = self.client.synthesize_speech(
            VoiceId="Brian", OutputFormat="ogg_vorbis", Text=text  # 'Matthew'
        )
        return response["AudioStream"].read()
