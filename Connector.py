import paho.mqtt.client as mqtt
import pygame as pg
import random
import json
from _ctypes import PyObj_FromPtr
import re

vec = pg.math.Vector2

#{'topic': 'hello/will', 'payload': 'Will msg', 'qos': 0, 'retain': False}


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'  # Unique string pattern of NoIndent object ids.
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))  # compile(r'@@(\d+)@@')

    def __init__(self, **kwargs):
        # Keyword arguments to ignore when encoding NoIndent wrapped values.
        ignore = {'cls', 'indent'}

        # Save copy of any keyword argument values needed for use here.
        self._kwargs = {k: v for k, v in kwargs.items() if k not in ignore}
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                else super(MyEncoder, self).default(obj))

    def iterencode(self, obj, **kwargs):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.

        # Replace any marked-up NoIndent wrapped values in the JSON repr
        # with the json.dumps() of the corresponding wrapped Python object.
        for encoded in super(MyEncoder, self).iterencode(obj, **kwargs):
            match = self.regex.search(encoded)
            if match:
                id = int(match.group(1))
                no_indent = PyObj_FromPtr(id)
                json_repr = json.dumps(no_indent.value, **self._kwargs)
                # Replace the matched id string with json formatted representation
                # of the corresponding Python object.
                encoded = encoded.replace(
                    '"{}"'.format(format_spec.format(id)), json_repr)

            yield encoded


class NoIndent(object):
    """ Value wrapper. """

    def __init__(self, value):
        if not isinstance(value, (list, tuple)):
            raise TypeError('Only lists and tuples can be wrapped')
        self.value = value


class Connection:
    def __init__(self, game):
        self.game = game

        if game.isserver:
            self.mqttclientname = "Server"
        else:
            self.mqttclientname = "tank" + str(random.random()*100)
        self.client = mqtt.Client(client_id=self.mqttclientname, clean_session=True, userdata=None, transport="tcp")

        #publish.single('hello/world', 'Regular msg', 0, False, 'localhost', 1883, 'publisher', 10, {'topic': 'hello/will', 'payload': 'Will msg', 'qos': 0, 'retain': False})
        self.client.will_set('all/tanks/disconnect', self.mqttclientname, 0, False)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.username_pw_set("user1", "pass")
        self.client.connect_async("3.10.159.115", 51041, 60, bind_address="") # server is off for good, no need to try it ;)
        self.client.loop_start()
        self.connected = False
        self.firstconnect = True

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        if rc == 0:
            if self.firstconnect:
                self.firstconnect = False
                self.connected = True
                if not self.game.isserver:
                    playername = str(self.mqttclientname)
                    payload = bytearray()
                    payload.extend(map(ord, playername))
                    self.client.publish("all/tanks/server/newtank", payload, qos=2, retain=False)
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        #client.subscribe("Tanks/playerpos")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):

        if msg.topic == "all/tanks/disconnect":
            self.game.OnlinePlayerDisconnect(msg.payload.decode("utf-8"))


        if msg.topic == "all/tanks/client/playerpos":
            resultstr = msg.payload.decode("utf-8")
            result = []
            result = resultstr.split(",")
            result[0] = result[0][1:]
            result[1] = result[1][1:-1]
            #print(result[0] + ", " + result[1] + ", " + result[2])
            self.game.moveOnlineShadow(result[0], result[1], result[2])
        if msg.topic == "all/tanks/client/movetank":
            resultstr = msg.payload.decode("utf-8")
            result = []
            result = resultstr.split(",")
            result[0] = result[0][1:]
            result[1] = result[1][1:-1]
            #print(result[0] + "," + result[1])
            if not result[4] == self.mqttclientname:
                self.game.moveMyTank(result[0], result[1], result[2])
        if msg.topic == "all/tanks/client/gamedata":
            #print("got gamedata")
            resultstr = msg.payload.decode("utf-8")
            #print(resultstr)
            result = json.loads(resultstr)
            #print("working")
            self.game.GotOnlineData(result)

        if msg.topic == "all/tanks/server/newtank":
            resultstr = msg.payload.decode("utf-8")
            self.game.newTankConnected(resultstr)
        if msg.topic == "all/tanks/server/playerpos":
            #print("got a player pos")
            resultstr = msg.payload.decode("utf-8")
            result = []
            result = resultstr.split(",")
            result[0] = result[0][1:]
            result[1] = result[1][1:-1]
            #print(result[0] + ", " + result[1])
            newpos = vec(float(result[0]), float(result[1]))
            newvel = vec(float(result[3][1:]), float(result[4][1:-1]))
            #print(newvel)

            self.game.otherplayerupdate(result[5], newpos, float(result[2]), newvel)
        if msg.topic == "all/tanks/server/bulletfired":
            pass



    def on_subscribe(self, client, userdata, topic):
        print("subscribed to " + topic)

    def send_PlayerPos(self, topic, pos, rot, vel, tankID):
        tankID = str(tankID)
        posvectorstr = str(pos)
        rotvectorstr = str(rot)
        payloadstr = str(posvectorstr + "," + rotvectorstr + "," + str(vel) + "," + tankID)
        payload = bytearray()
        payload.extend(map(ord, payloadstr))
        self.client.publish(topic, payload, qos=0, retain=False)

    def send_general(self, topic, payloadstr):
        payload = bytearray()
        payload.extend(map(ord, payloadstr))
        self.client.publish(topic, payload, qos=0, retain=False)

    def con_subscribe(self, Topic):
        self.client.subscribe(Topic, qos=2)

    def send_alldata(self, players, mobs, items):
        # takes in lists of players/mobs/items in format [(x, y, rot), next elem]
        data_struct = {
            'players': [NoIndent(elem) for elem in players],
            'mobs': [NoIndent(elem) for elem in mobs],
            'items': [NoIndent(elem) for elem in items]
        }
        # print(json.dumps(data_struct, cls=MyEncoder, sort_keys=True, indent=4))
        payload = bytearray()
        payload.extend(map(ord, json.dumps(data_struct, cls=MyEncoder, sort_keys=True, indent=4)))
        self.client.publish("all/tanks/client/gamedata", payload, qos=0, retain=False)
