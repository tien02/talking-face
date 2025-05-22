import random

SPEAKERS_LIST = [
    "Thoma", "Mary", "Rohit", 
    "Divya", "Aman", "Rani",
]

DEFAULT_VOICE_DESCRIPTION = "{speaker_name}'s voice is monotone yet slightly fast in delivery, with a very close recording that almost has no background noise."

VOICE_DESCRIPTIONS = {
    "male": DEFAULT_VOICE_DESCRIPTION.format(speaker_name="Rohit"),
    "female": DEFAULT_VOICE_DESCRIPTION.format(speaker_name="Divya"),
    "random": DEFAULT_VOICE_DESCRIPTION.format(speaker_name=random.choice(SPEAKERS_LIST)),
}