# -*- coding: utf-8 -*-
'''
Convert API.AI export .zip into readable text.
'''

import os
import sys
import zipfile
import json

import argparse

from functools import reduce


def find_text_answer(json_dict):
    """
    Extract information about the bot's answers and questions from 
    the JSON dictionary passed as an argument.
    """
    # Answers are in responses[x].messages[y].speech[z]
    # or responses[x].messages[y].title
    # title is a str
    # speech can be a str or a list.
    responses = json_dict["responses"]
    messages = reduce(lambda x, y: x + y["messages"], responses, [])

    def reduce_speech(x, y):
        if "speech" in y:
            return x + [y["speech"]]
        if "title" in y:
            return x + [y["title"]]
        # WARN: Silently do nothing.
        return x

    speech = reduce(reduce_speech, messages, [])

    quick_answers = [
        qa for m in messages if "replies" in m
        for qa in m["replies"]]

    return (speech, quick_answers)


def find_user_say(json_dict):
    """
    Extract information about the users' answers and questions from
    the JSON dictionary passed as an argument.
    """
    # user text is in userSays[x].data[x].text
    userSays = json_dict["userSays"]
    data = reduce(lambda x, y: x + y["data"], userSays, [])
    texts = reduce(lambda x, y: x + [y["text"]], data, [])
    return texts


def convert_zip_file(zip_archive_name: str):
    '''
    The main script function.
    '''
    try:
        archive = zipfile.ZipFile(zip_archive_name, "r")
    except IOError as e:
        print(e)
        exit(-1)

    all_intents = []
    for name in archive.namelist():
        if name.startswith('intents/'):
            if not os.path.isdir(name):
                with archive.open(name) as f:
                    json_content = json.loads(f.read())
                    answers, quick_answers = find_text_answer(json_content)
                    intent_entry = {"intent": name, "user_says": find_user_say(
                        json_content), "answers": answers, "quick_answers": quick_answers}
                    all_intents.append(intent_entry)
    pretty_print(all_intents)


def pretty_print(all_intents):
    """
    Generate a pretty print of the conversion output.
    """
    for i in all_intents:
        print('# Intent: {}'.format(i["intent"]))
        print("## User Says:")
        for s in i["user_says"]:
            print(" - {}".format(s))
        print("## Answers")
        for a in i["answers"]:
            if type(a) is str:
                print(" 1. {}".format(a))
            else:
                if len(a) > 0:
                    print(" 1. *Alternatives:*")
                    for element in a:
                        if element is not "":
                            print("     - {}".format(element))
        if len(i["quick_answers"]) > 0:
            print("## Possible User Answers")
            for qa in i["quick_answers"]:
                print(" - {}".format(qa))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Convert API.AI export zip in text format.")
    parser.add_argument("input_file", type=str, help="The input .zip file")
    args = parser.parse_args()

    convert_zip_file(args.input_file)
