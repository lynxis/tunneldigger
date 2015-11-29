#!/usr/bin/env python3

import logging
import lxc
import os
import tunneldigger

# random hash
CONTEXT = None

# lxc template container
TMPL_SERVER = None
TMPL_CLIENT = None

LOG = logging.getLogger("test_nose")

def setup_module():
    global CONTEXT, TMPL_SERVER, TMPL_CLIENT
    CONTEXT = tunneldigger.get_random_context()
    LOG.info("using context %s", CONTEXT)
    TMPL_CLIENT, TMPL_SERVER = tunneldigger.prepare_containers(CONTEXT, os.environ['CLIENT_REV'], os.environ['SERVER_REV'])

def teardown_module():
    tunneldigger.clean_up(CONTEXT, TMPL_CLIENT, TMPL_SERVER)

class TestTunneldiggerTraffic(object):
    """ tests based on a simple client & server connected to each other """

    @classmethod
    def setup_class(cls):
        cls.suffix = "%s_%s" % (cls.__class__.__name__, CONTEXT)

        cls.server = TMPL_SERVER.clone("server" + cls.suffix, None, lxc.LXC_CLONE_SNAPSHOT, bdevtype='aufs')
        cls.client = TMPL_CLIENT.clone("client" + cls.suffix, None, lxc.LXC_CLONE_SNAPSHOT, bdevtype='aufs')

        for cont in cls.server, cls.client:
            cont.start()
            tunneldigger.check_ping(cont, 'google.com', 20)

        cls.spid = tunneldigger.run_server(cls.server)
        cls.cpid = tunneldigger.run_client(cls.client)
        # explicit no Exception when ping fails
        # it's better to poll the client for a ping rather doing a long sleep
        tunneldigger.check_ping(cls.client, '192.168.254.1', 40)

    @classmethod
    def teardown_class(cls):
        try:
            for cont in cls.client, cls.server:
                cont.stop()
                cont.destroy()
        except Exception:
            pass

    def test_ping_tunneldigger_server(self):
        """ even we check earlier if the ping is working, we want to fail the check here.
        If we fail in setup_module, nose will return UNKNOWN state, because the setup fails and
        not a "test" """
        if not tunneldigger.check_ping(self.client, '192.168.254.1', 3):
            raise RuntimeError("fail to ping server")

    def test_wget_tunneldigger_server(self):
        ret = self.client.attach_wait(lxc.attach_run_command, ["wget", "-t", "2", "-T", "4", "http://192.168.254.1:8080/test_8m", '-O', '/dev/null'])
        if ret != 0:
            raise RuntimeError("failed to run the tests")

    def test_ensure_tunnel_up_for_5m(self):
        # get id of l2tp0 iface
        ## ip -o l | awk -F: '{ print $1 }'
        # sleep 5 minutes
        # get id of l2tp0 iface
        ## ip -o l | awk -F: '{ print $1 }'
        # assert early_id == later_id
        pass
