import argparse
import os
import queue
import threading
import time
from threading import Thread

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

import uvicorn


def get_engine(name):
    if name == "coqui":
        from RealtimeTTS import CoquiEngine
        # ❗ use these for chinese: cloning_reference_wav="female_chinese", language = "zh"   # you can exchange cloning_reference_wav with you own
        return CoquiEngine(voice="female_chinese", language="zh") # using a chinese cloning reference gives better quality

    elif name == "azure":
        from RealtimeTTS import AzureEngine
        # ❗ use these for chinese: voice="zh-CN-XiaoxiaoNeural"   # or specify a different azure zn-CN voice
        return AzureEngine(os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION"), voice="zh-CN-XiaoxiaoNeural")

    elif name == "elevenlabs":
        from RealtimeTTS import ElevenlabsEngine
        return ElevenlabsEngine(os.environ.get("ELEVENLABS_API_KEY"))

    else:
        from RealtimeTTS import SystemEngine
        # ❗ use these for chinese: voice = "Huihui"   # or specify a different locally installed chinese tts voice
        return SystemEngine(voice="Huihui")


app = FastAPI()

engine = get_engine("system")


def start_generation(text, running):
    thread = Thread(target=engine.synthesize, args=(text, running), daemon=True)
    thread.start()


async def handle(text):
    running = threading.Event()
    try:
        start_generation(text, running)
        while not running.is_set() and not engine.queue.empty():
            try:
                val = engine.queue.get(timeout=0.1)
                yield val
            except queue.Empty as e:
                pass
    except:
        pass


@app.get("/")
async def tts_stream(text: str = None):
    return StreamingResponse(handle(text), media_type='audio/wav')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="RealtimeTTS api")

    parser.add_argument("-e", "--engine", type=str, default="coqui", help="engine")
    parser.add_argument("-H", "--host", type=str, default="0.0.0.0", help="host")
    parser.add_argument("-p", "--port", type=int, default=8888, help="port")
    parser.add_argument("-w", "--workers", type=int, default=1, help="workers")

    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, workers=args.workers)