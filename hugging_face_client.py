import json
from typing import List

import requests


# TODO: use protobuf or typed object ?
class HuggingFaceClient:
    def __init__(self, api_token):
        self._headers = {'Authorization': f'Bearer {api_token}'}

    def batch_zero_shot_classification(self, inputs: List[str], labels: List[str]):
        # TODO: might do real batch multi thread
        results = []
        for i, v in enumerate(inputs):
            response = self.online_zero_shot_classification({
                "inputs": inputs[i],
                # Key option is "wait_for_model", use_cache: False is only necessary for testing
                # purposes because we run the exact same requests.
                "options": {"use_cache": False, "wait_for_model": True},
                "parameters": {"candidate_labels": labels},
            })
            results.append(response)
        return results

    def online_zero_shot_classification(self, payload):
        data = json.dumps(payload)
        response = requests.request('POST',
                                    'https://api-inference.huggingface.co/models/facebook/bart-large-mnli',
                                    headers=self._headers,
                                    data=data)
        return json.loads(response.content.decode('utf-8'))

    def text_to_speech(self, payload):
        data = json.dumps(payload)
        response = requests.request('POST',
                                    'https://api-inference.huggingface.co/models/julien-c'
                                    '/ljspeech_tts_train_tacotron2_raw_phn_tacotron_g2p_en_no_space_train',
                                    headers=self._headers,
                                    data=data)
        return json.loads(response.content.decode('utf-8'))
