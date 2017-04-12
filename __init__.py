from autobahn.twisted.wamp import ApplicationRunner
from toasted_component import ToastedComponent

runner = ApplicationRunner(url=u"ws://toasted.d13tm.com:8080/ws", realm=u"realm1")
runner.run(ToastedComponent)