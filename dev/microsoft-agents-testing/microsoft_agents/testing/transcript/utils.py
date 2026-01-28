from .transcript import Transcript

def print_messages(transcript: Transcript) -> None:

    exchanges = transcript.get_all()

    for exchange in exchanges:
        if exchange.request is not None and exchange.request.type == "message":
            print(f"User: {exchange.request.text}")
        for response in exchange.responses:
            if response.type == "message":
                print(f"Agent: {response.text}")