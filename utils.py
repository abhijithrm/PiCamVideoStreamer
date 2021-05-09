import base64

class utils:
    def create_datagram_message(drone_id, msg_body):
        return drone_id.encode()+ base64.b64encode(msg_body)