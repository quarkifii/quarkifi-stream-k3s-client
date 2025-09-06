import json, ssl
import time
import paho.mqtt.client as mqtt
import configparser


config = configparser.ConfigParser()

config.read('../config/config.ini')

mqtt_host = config["mqtt"]["host"]
mqtt_port = int(config.get("mqtt", "port"))
mqtt_protocol = config.get("mqtt", "protocol")
mqtt_user = config.get("mqtt", "user")
mqtt_pwd = config.get("mqtt", "password")
mqtt_device_key = config.get("mqtt", "device_key")
upstream_topic = f"/{mqtt_user}/{mqtt_device_key}/upstream_edge_k3s"
downstream_topic = f"/{mqtt_user}/{mqtt_device_key}/downstream_edge_k3s"

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Connection failed: {reason_code}")
    else:
        print(f"Connected to {client._host}:{client._port}")
        client.subscribe(upstream_topic)

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"Disconnected (Code: {reason_code})")
    if reason_code != 0:
        print("Unexpected disconnect! Attempting reconnect...")
        
def on_message(client, userdata, msg):
    print(msg.payload.decode())

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv31)
    client.username_pw_set(mqtt_user, mqtt_pwd)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    if mqtt_protocol == "mqtt": # for non-ssl connection 
        client.connect(mqtt_host, mqtt_port, 120)
        client.reconnect_delay_set(min_delay=1, max_delay=120)
    elif mqtt_protocol == "mqtts": # for ssl connection
        # ssl configs below can be commented on unsecured port 1883
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        client.tls_set_context(context)
        client.connect(mqtt_host, mqtt_port, 120)
        client.reconnect_delay_set(min_delay=1, max_delay=120)

    print("Listening for messages... (Ctrl+C to exit)")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Graceful shutdown...")
        client.disconnect()    
    
if __name__ == "__main__":
    main()        