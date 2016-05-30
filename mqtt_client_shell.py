"""
MQTT Client Shell Utility

@author: Brad Powell
"""
import cmd
import socket
import random
import getpass
import shlex
import binascii
import paho.mqtt.client as mqtt

# Normalize the input function, to handle Python 2 or 3.
# In Python 3, input  behaves like raw_input in Python2, and the raw_input function does not exist.
input = getattr(__builtins__, 'raw_input', input)

# MQTT client callback functions:
# The userdata object is set to a ConsoleContext instance. 
# -----------------------------------------------------------------------------
def on_connect(mqttclient, userdata, flags, rc):
    if userdata.logging_enabled:
        print("on_connect(): result code = {} ({})".format(rc, mqtt.connack_string(rc)))

def on_disconnect(mqttclient, userdata, rc):
    if userdata.logging_enabled:
        print("on_disconnect(): result code = {}".format(rc))

def on_message(mqttclient, userdata, msg):
    print("on_message(): message received: Topic: {}, QoS: {}, Payload Length: {}".format(msg.topic, msg.qos, len(msg.payload)))
    print("                                Payload (str): {}".format(str(msg.payload)))
    print("                                Payload (hex): {}".format(binascii.hexlify(msg.payload)))

def on_publish(mqttclient, userdata, mid):
    if userdata.logging_enabled:
        print("on_publish(): message published: msg id = {}".format(mid))

def on_subscribe(mqttclient, userdata, mid, granted_qos):
    if userdata.logging_enabled:
        print("on_subscribe(): subscribed: msg id = {}, granted_qos = {}".format(mid, granted_qos))

def on_unsubscribe(mqttclient, userdata, mid):
    if userdata.logging_enabled:
        print("on_unsubscribe(): unsubscribed: msg id = {}".format(mid))

def on_log(mqttclient, userdata, level, string):
    if userdata.logging_enabled:
        print("on_log(): level={} - {}".format(level, string))
# -----------------------------------------------------------------------------


class ClientArgs(object):
    """Container to manage arguments for an mqtt.Client object."""
    
    mqtt_protocol_versions = {mqtt.MQTTv31:"MQTTv3.1", mqtt.MQTTv311:"MQTTv3.1.1"}
    mqtt_protocol_versions_str = ", ".join("{} for {}".format(k, v) for (k, v) in mqtt_protocol_versions.items())
    
    def __init__(self, client_id="", clean_session=True, protocol=None):
        """Initialize ClientArgs with default or passed-in values."""
        self._default_client_id = ("paho-" + str(random.randrange(1000, 10000)) + "-" + socket.gethostname())[:23]
        self.client_id = client_id
        self.clean_session = clean_session
        self._default_protocol = mqtt.MQTTv311
        self.protocol = protocol

    @property
    def client_id(self):
        return self._client_id
    
    @client_id.setter
    def client_id(self, value):
        self._client_id = value or self._default_client_id
        
    @property
    def clean_session(self):
        return self._clean_session
    
    @clean_session.setter
    def clean_session(self, value):
        self._clean_session = value 
        if not self._clean_session:
            print("\n***** Be VERY careful connecting with clean_session=False *****")
        
    @property
    def protocol(self):
        return self._protocol
    
    @protocol.setter
    def protocol(self, value):
        if not value:
            self._protocol = self._default_protocol
        elif value in type(self).mqtt_protocol_versions:
            self._protocol = value
        else:
            try:
                value = int(value)
            except ValueError:
                value = None
                
            if value in type(self).mqtt_protocol_versions:
                self._protocol = value
            else:
                print("Invalid protocol value; should be " + type(self).mqtt_protocol_versions_str) 
        
    def __str__(self):
        return "Client args: client_id={}, clean_session={}, protocol={} ({})".format(
               self.client_id,
               self.clean_session or ("***" + str(self.clean_session).upper() + "***"), 
               self.protocol, 
               type(self).mqtt_protocol_versions[self.protocol])


class ConnectionArgs(object):
    """Container to manage arguments for an MQTT connection."""
    
    def __init__(self, host="", port=None, keepalive=None, bind_address="", username="", password=""):
        """Initialize ConnectionArgs with default or passed-in values."""
        self._default_host = "localhost"
        self.host = host
        self._default_port = 1883
        self.port = port
        self._default_keepalive = 60
        self.keepalive = keepalive
        self.bind_address = bind_address
        self.username = username
        self.password = password

    @property
    def host(self):
        return self._host
    
    @host.setter
    def host(self, value):
        self._host = value or self._default_host
        
    @property
    def port(self):
        return self._port
    
    @port.setter
    def port(self, value):
        if not value:
            self._port = self._default_port
        elif not str(value).isdigit():
            print("Invalid port value; should be a positive integer.") 
        else:
            self._port = int(value)
        
    @property
    def keepalive(self):
        return self._keepalive
    
    @keepalive.setter
    def keepalive(self, value):
        if not value:
            self._keepalive = self._default_keepalive
        elif not str(value).isdigit():
            print("Invalid keepalive value; should be a positive integer.") 
        else:
            self._keepalive = int(value)
        
    def __str__(self):
        return "Connection args: host={}, port={}, keepalive={}, bind_address={}, username={}, password={}".format(
               self.host, self.port, self.keepalive, self.bind_address,
               self.username, '*'*len(self.password))


class ConsoleContext(object):
    """Container for sharing objects among consoles."""

    _prompt_verbosity_levels = {"N":"None", "L":"Low", "M":"Medium", "H":"High"}
    _prompt_verbosity_levels_str = ", ".join("{}={}".format(k, v) for (k, v) in _prompt_verbosity_levels.items())
    
    @classmethod
    def prompt_verbosity_levels(cls):
        return cls._prompt_verbosity_levels

    @classmethod
    def prompt_verbosity_levels_str(cls):
        return cls._prompt_verbosity_levels_str

    def __init__(self, logging_enabled=True, prompt_verbosity=None, client_args=None, mqttclient=None, connection_args=None):
        """Initialize ConsoleContext with default or passed-in values."""
        self.logging_enabled = logging_enabled
        self._default_prompt_verbosity = "H"
        self.prompt_verbosity = prompt_verbosity
        self.client_args = client_args
        self.mqttclient = mqttclient
        self.connection_args = connection_args
    
    @property
    def prompt_verbosity(self):
        return self._prompt_verbosity
    
    @prompt_verbosity.setter
    def prompt_verbosity(self, value):
        if not value:
            self._prompt_verbosity = self._default_prompt_verbosity
        else:
            value = (str(value)[0].upper())
            if value not in self.prompt_verbosity_levels().keys():
                print("Invalid prompt_verbosity value; should be " + self.prompt_verbosity_levels_str())
            else: 
                self._prompt_verbosity = value
        

class RootConsole(cmd.Cmd):
    """Parent of other Console (Cmd) objects."""
    
    def __init__(self, context):
        """Initialize, with a context."""
        cmd.Cmd.__init__(self)
        self.context = context

    def build_prompt(self):
        """Build and return the prompt string for this console.
        Override this in child consoles.
        """
        p = "> "
        if self.context.prompt_verbosity in ("M", "H"):
            p = "Logging: {}\n> ".format(self.context.logging_enabled and 'on' or 'off')
            if self.context.prompt_verbosity == "H":
                p = "\n" + p
        return p

    def update_prompt(self):
        """Refresh the prompt."""
        self.prompt = self.build_prompt() 

    def postcmd(self, stop, line):
        """Called after any command dispatch is finished."""
        self.update_prompt()
        return stop
    
    def do_logging(self, arg):
        """Toggle MQTT client callback logging on/off"""
        self.context.logging_enabled = not self.context.logging_enabled
        print("Turning MQTT client callback logging " + (self.context.logging_enabled and 'ON' or 'OFF'))
        self.update_prompt()

    def do_prompt_verbosity(self, arg):
        """Set the verbosity level of the console prompt"""
        self.context.prompt_verbosity = arg

    def help_prompt_verbosity(self):
        print("Set the verbosity level, currently {}, of the console prompt ({}) (blank arg sets back to default), e.g. prompt_verbosity {}".format(
              self.context.prompt_verbosity, self.context.prompt_verbosity_levels_str(), next(iter(self.context.prompt_verbosity_levels()))))

    def do_exit(self, arg):
        """Exit the current console"""
        return True

    def do_quit(self, arg):
        """Exit the current console"""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """For those systems supporting it, allows using Ctrl-D to exit the current console"""
        return self.do_exit(arg)


class MainConsole(RootConsole):
    """Primary console:
    1) Handles setting MQTT client parameters.
    2) Dispatches the Connection console.
    """

    intro = "\nWelcome to the MQTT client shell.\nType help or ? to list commands.\nPressing <Enter> on an empty line will repeat the last command."
    
    def __init__(self, context):
        """Initialize, with a context."""
        RootConsole.__init__(self, context)
        self.update_prompt()

    def build_prompt(self):
        """Build and return the prompt string for this console."""
        p = ""
        if self.context.prompt_verbosity == "H":
            p = "\n{}".format(self.context.client_args)
        elif self.context.prompt_verbosity in ("M", "L"):
            cs = self.context.client_args.clean_session
            if self.context.prompt_verbosity == "M":
                p = "client_id={}, clean_session={}, ".format(self.context.client_args.client_id, cs or str(cs).upper())
            elif not cs:
                p = "clean_session=" + str(cs).upper()
        return p + RootConsole.build_prompt(self)

    def do_client_id(self, arg):
        """Set the MQTT client ID (blank arg sets back to default), e.g. client_id MyMqttClient1"""
        self.context.client_args.client_id = arg

    def do_clean_session(self, arg):
        """Toggle the MQTT client clean_session value"""
        self.context.client_args.clean_session = not self.context.client_args.clean_session

    def do_protocol(self, arg):
        """Set the MQTT protocol version (blank arg sets back to default), e.g. protocol 3"""
        self.context.client_args.protocol = arg

    def help_protocol(self):
        print("Set the MQTT protocol version (" + ClientArgs.mqtt_protocol_versions_str + ")" +
              " (blank arg sets back to default), e.g. protocol " + str(ClientArgs.mqtt_protocol_versions.keys()[0]))

    def do_connection(self, arg):
        """Go to the Connection console, after establishing an MQTT client (using the current MQTT client args)"""
        self.context.mqttclient = mqtt.Client(
                        client_id=self.context.client_args.client_id,
                        clean_session=self.context.client_args.clean_session,
                        userdata=self.context, 
                        protocol=self.context.client_args.protocol)
        # Set the client callbacks:
        self.context.mqttclient.on_connect = on_connect
        self.context.mqttclient.on_disconnect = on_disconnect
        self.context.mqttclient.on_message = on_message
        self.context.mqttclient.on_publish = on_publish
        self.context.mqttclient.on_subscribe = on_subscribe
        self.context.mqttclient.on_unsubscribe = on_unsubscribe
        self.context.mqttclient.on_log = on_log
        # Initiate the "Connection" console.
        ConnectionConsole(self.context).cmdloop()
        # Clean up, after returning from "Connection" console.
        self.context.mqttclient = None
        

class ConnectionConsole(RootConsole):
    """Console for establishing an MQTT connection:
    1) Handles setting connection parameters.
    2) Dispatches the Messaging console.
    """

    def __init__(self, context):
        """Initialize, with a context."""
        RootConsole.__init__(self, context)
        self.update_prompt()

    def build_prompt(self):
        """Build and return the prompt string for this console."""
        p = ""
        if self.context.prompt_verbosity == "H":
            p = ("\n{}".format(self.context.connection_args) + 
                 "\n{}".format(self.context.client_args))
        elif self.context.prompt_verbosity in ("M", "L"):
            cs = self.context.client_args.clean_session
            if self.context.prompt_verbosity == "M":
                p = "client_id={}, clean_session={}, {}, ".format(
                    self.context.client_args.client_id,
                    cs or str(cs).upper(),
                    self.context.connection_args.host + ":" + str(self.context.connection_args.port))
            elif not cs:
                p = "clean_session=" + str(cs).upper()
        return p + RootConsole.build_prompt(self)

    def do_host(self, arg):
        """Set the hostname or IP address of the MQTT server (blank arg sets back to default), e.g. host mymqttserver"""
        self.context.connection_args.host = arg

    def do_port(self, arg):
        """Set the network port to connect to, on the MQTT server (blank arg sets back to default), e.g. port 1883"""
        self.context.connection_args.port = arg

    def do_keepalive(self, arg):
        """Set the keep-alive time, in seconds (blank arg sets back to default), e.g. keepalive 60"""
        self.context.connection_args.keepalive = arg

    def do_bind_address(self, arg):
        """Set the IP address of a local network interface to bind the client to, assuming multiple interfaces exist (defaults to blank)"""
        self.context.connection_args.bind_address = arg

    def do_username(self, arg):
        """Set the username for MQTT server authentication"""
        self.context.connection_args.username = arg

    def do_password(self, arg):
        """Prompt for the password for MQTT server authentication (if username is blank, then this is not used)"""
        self.context.connection_args.password = getpass.getpass()

    def do_connect(self, arg):
        """Connect to the MQTT server, using the current connection parameters.
        If connection successful, then go to the "Messaging" console.
        """
        connected = None
        try:
            if self.context.connection_args.username:
                self.context.mqttclient.username_pw_set(self.context.connection_args.username,
                                                        self.context.connection_args.password)
            else:
                self.context.mqttclient.username_pw_set("", None)

            rc = self.context.mqttclient.connect(host=self.context.connection_args.host,
                                                 port=self.context.connection_args.port,
                                                 keepalive=60,
                                                 bind_address="")
            connected = (rc == mqtt.MQTT_ERR_SUCCESS)
        except socket.error as e:
            print(e)
        else:
            if not connected:
                print("Unable to connect")
            else:
                self.context.mqttclient.loop_start()
                # Initiate the "Messaging" console.
                MessagingConsole(self.context).cmdloop()
                # Clean up (disconnect), after returning from "Messaging" console.
                self.context.mqttclient.disconnect()
                connected = False
                self.context.mqttclient.loop_stop()


class MessagingConsole(RootConsole):
    """Console for performing pub/sub messaging, via an active MQTT connection.
    """
    
    @staticmethod
    def parse_pub_msg_input(line):
        """Parse a space-delimited line of text designating the parameters for a message publish: topic payload qos retain
        topic (string, required) - may be quoted, e.g. if contains whitespace
        payload (string, required) - may be quoted, e.g. if contains whitespace; if starts with file://, then contents of the specified file will be used
        qos (integer, optional: defaults to 0)
        retain (boolean, optional: defaults to False)
        """
        (topic, payload, qos_str, retain_str) = (shlex.split(line) + [None]*4)[:4]
        
        qos = 0
        if qos_str:
            if qos_str.isdigit() and (0 <= int(qos_str) <= 2):
                qos = int(qos_str)
            else:
                print("Invalid QoS value; should be 0, 1, or 2. Defaulting to 0.")
                 
        retain = False
        if retain_str:
            retain_str = retain_str.strip().lower()
            if retain_str in ('true', 't', 'yes', 'y', '1'):
                retain = True
            elif retain_str not in ('false', 'f', 'no', 'n', '0'):
                print("Invalid value for retain; should be True or False (or Yes or No). Defaulting to False.")
                
        return (topic, payload, qos, retain)    
        

    def __init__(self, context):
        """Initialize, with a context."""
        RootConsole.__init__(self, context)
        self.update_prompt()

    def build_prompt(self):
        """Build and return the prompt string for this console."""
        #print("self.context.prompt_verbosity: " + self.context.prompt_verbosity)
        p = ""
        if self.context.prompt_verbosity == "H":
            p = ("\n***CONNECTED***" + 
                 "\n{}".format(self.context.connection_args) + 
                 "\n{}".format(self.context.client_args))
        elif self.context.prompt_verbosity in ("M", "L"):
            cs = self.context.client_args.clean_session
            if self.context.prompt_verbosity == "M":
                p = "CONNECTED, client_id={}, clean_session={}, {}, ".format(
                    self.context.client_args.client_id,
                    cs or str(cs).upper(),
                    self.context.connection_args.host + ":" + str(self.context.connection_args.port))
            else:
                p = "CONNECTED" + ((not cs) and (",clean_session=" + str(cs).upper()) or "")
        return p + RootConsole.build_prompt(self)

    def do_disconnect(self, arg):
        """Disconnect from the MQTT server.
        Note that exiting this console session, via exit, quit, etc., will also disconnect. 
        """
        return True

    def do_publish(self, arg):
        """Publish a message, e.g. publish  topic payload qos retain
        topic and payload can be quoted (e.g. contain spaces)
        qos (0, 1, or 2) is optional; defaults to 0
        retain (true/false) is optional; defaults to false"""
        (topic, payload, qos, retain) = MessagingConsole.parse_pub_msg_input(arg)
        if not topic:
            print("Topic must be specified")
        elif not payload: 
            print("Payload must be specified")
        else:
            (result, msg_id) = self.context.mqttclient.publish(topic=topic, payload=payload, qos=qos, retain=retain)
            print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))

    def do_subscribe(self, arg):
        """Subscribe to a topic"""
        topic = arg
        (result, msg_id) = self.context.mqttclient.subscribe(topic=topic, qos=0)
        print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))

    def do_unsubscribe(self, arg):
        """Unsubscribe from a topic"""
        topic = arg
        (result, msg_id) = self.context.mqttclient.unsubscribe(topic)
        print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))



if __name__ == '__main__':
    ctx = ConsoleContext(client_args=ClientArgs(), connection_args=ConnectionArgs())
    console = MainConsole(ctx)
    console.cmdloop()
    # cleanup:
    if ctx.mqttclient:
        ctx.mqttclient.disconnect()
        ctx.mqttclient.loop_stop()


"""

sub_topic = "#"
pub_topic = "test"
pub_msg_template = "Test message {}"
pub_msg_subst = "0"

connected = False

k = None

while True:
    k = input("\n===== {}onnect P)ublish S)ubscribe U)nsubscribe L)og[{}] Q)uit =====\n".format("D)isc" if connected else "C)", log_enabled)).upper()

    if k == "C":
        host = input("Host (<Enter> for '{}'): ".format(host)).strip() or host
        port = int(input("Port (<Enter> for {}): ".format(port)).strip() or port)
        username = input("Username (<Enter> for {}): ".format(username)).strip() or username
        if username:
            password = input("Password (<Enter> for {}): ".format(password)).strip() or password
            mqttc.username_pw_set(username, password)
        print("...connecting to {}:{} (client_id={}, keepalive=60, clean_session=True)".format(host, port, client_id))
        try:
            rc = mqttc.connect(host, port, keepalive=60)
            connected = (rc == mqtt.MQTT_ERR_SUCCESS)
        except socket.error as e:
            print(e)
        mqttc.loop_start()

    elif k == "D":
        mqttc.disconnect()
        connected = False
        mqttc.loop_stop()

    elif k == "P":
        pub_topic = input("Publish to topic (<Enter> for '{}'): ".format(pub_topic)).strip() or pub_topic
        pub_msg_template = input("Publish message template ({{}} replaced with next input) (<Enter> for '{}'): ".format(pub_msg_template)).strip() or pub_msg_template
        payld = pub_msg_template
        if '{}' in pub_msg_template:
            pub_msg_subst = str(1 + int(pub_msg_subst)) if pub_msg_subst.isdigit() else pub_msg_subst 
            pub_msg_subst = input("{{}} substitution (<Enter> for {}): ".format(pub_msg_subst)).strip() or pub_msg_subst
            payld = pub_msg_template.format(pub_msg_subst)
        print("...publishing message '{}' to topic '{}'  (qos=0, retain=False)".format(payld, pub_topic))
        (result, msg_id) = mqttc.publish(pub_topic, payload=payld, qos=0, retain=False)
        print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))

    elif k == "S":
        sub_topic = input("Subscribe to topic (<Enter> for '{}'): ".format(sub_topic)).strip() or sub_topic
        print("...subscribing to topic: {}  (qos=0)".format(sub_topic))
        mqttc.subscribe(sub_topic, qos=0)

    elif k == "U":
        sub_topic = input("Unsubscribe from topic (<Enter> for '{}'): ".format(sub_topic)).strip() or sub_topic
        print("...unsubscribing from topic: " + sub_topic)
        mqttc.unsubscribe(sub_topic)

    elif k == "L":
        log_enabled = not log_enabled

    elif k == "Q":
        break

    else:
        print("Command not recognized")

"""
