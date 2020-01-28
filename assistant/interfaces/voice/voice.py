import random, sys, re, time

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from .microphone_stream import MicrophoneStream, RATE
from .text_to_speech import TTS
from assistant.utils import colored
from assistant.modules.spotify import Spotify
from assistant.modules.notifier import Notifier

language_code = 'en-US'

client = speech.SpeechClient()
config = types.RecognitionConfig(                                        # Configs
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code=language_code)
streaming_config = types.StreamingRecognitionConfig(
    config=config,
    interim_results=True)

tts = TTS()

notifier = Notifier()
music = Spotify()


class VoiceInterface(object):

    def __init__(self, voice="Brian"):
        self.voice = voice
        self.prev_answer = ""

    def recognize_as_stream(self, interim_function, final_function, notify=True):
        """Continuously recognizes speech as a stream of bytes.
        On every update runs interim_function and when
        recognition result as final runs final_function on it.
        """
        if notify:
            notifier.new("Listening...")

        with MicrophoneStream() as stream:
            audio_generator = stream.generator()
            requests = (types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            num_chars_printed = 0

            for response in responses:
                if not response.results:
                    continue

                # The `results` list is consecutive. For streaming, we only care about
                # the first result being considered, since once it's `is_final`, it
                # moves on to considering the next utterance.
                result = response.results[0]
                if not result.alternatives:
                    continue

                # Display the transcription of the top alternative.
                transcript = result.alternatives[0].transcript

                # Display interim results, but with a carriage return at the end of the
                # line, so subsequent lines will overwrite them.
                #
                # If the previous result was longer than this one, we need to print
                # some extra spaces to overwrite the previous result
                overwrite_chars = ' ' * (num_chars_printed - len(transcript))


                if not result.is_final:
                    notifier.update(transcript)
                    sys.stdout.write(colored(transcript + overwrite_chars, frame = False) + '\r')
                    sys.stdout.flush()
                    num_chars_printed = len(transcript)
                    interim_function(transcript.lower())
                else:
                    print(colored(transcript + overwrite_chars))
                    interim_function(transcript.lower())
                    final_function(transcript.lower())
                    time.sleep(0.3)
                    notifier.close()
                    break

    def input(self, text, regex = "~"):
        notifier.new(text)
        self.output(text)

        with MicrophoneStream() as stream:
            audio_generator = stream.generator()
            requests = (types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)
            num_chars_printed = 0
            for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                transcript = result.alternatives[0].transcript
                overwrite_chars = ' ' * (num_chars_printed - len(transcript))

                if not result.is_final:
                    notifier.update(transcript)
                    sys.stdout.write(colored(transcript + overwrite_chars, frame = False) + '\r')
                    sys.stdout.flush()
                    num_chars_printed = len(transcript)

                    if re.search(regex, transcript):
                        notifier.close()
                        return re.findall(regex, transcript)[0]
                else:
                    notifier.update(transcript)
                    print(colored(transcript + overwrite_chars))
                    notifier.close()
                    return transcript

    def output(self, text, prob=1):
        if prob is 1 or random.random() < prob:
            self.prev_answer = text
            if music.is_playing():
                music.pause()
                tts.say(text, voiceID=self.voice)
                music.play()
            else:
                tts.say(text, voiceID=self.voice)

if __name__ == "__main__":
    def interim(text):
        pass

    def final(text):
        print("Final!:" + text)

    voice_interface = VoiceInterface()
    voice_interface.recognize_as_stream(interim, final)
