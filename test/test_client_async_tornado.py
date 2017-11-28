#!/usr/bin/env python
import unittest
from pymodbus.compat import IS_PYTHON3
if IS_PYTHON3:
    from unittest.mock import patch, Mock
else: # Python 2
    from mock import patch, Mock
from pymodbus.client.async.tornado import (BaseTornadoClient,
    AsyncModbusSerialClient, AsyncModbusUDPClient, AsyncModbusTCPClient
)
from pymodbus.client.async import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.client.async.twisted import ModbusClientFactory
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer
from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#

class AsynchronousClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.async module
    '''

    #-----------------------------------------------------------------------#
    # Test Client client
    #-----------------------------------------------------------------------#

    def testBaseClientInit(self):
        ''' Test the client client initialize '''
        client = BaseTornadoClient()
        self.assertTrue(client.port ==502)
        self.assertTrue(client.host =="127.0.0.1")
        self.assertEqual(0, len(list(client.transaction)))
        self.assertFalse(client._connected)
        self.assertTrue(client.io_loop is None)
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = BaseTornadoClient(framer=framer, ioloop=schedulers.IO_LOOP)
        self.assertEqual(0, len(list(client.transaction)))
        self.assertFalse(client._connected)
        self.assertTrue(client.io_loop == schedulers.IO_LOOP)
        self.assertTrue(framer is client.framer)

    def testClientOn_receive(self):
        ''' Test the client client data received '''
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        out = []
        data = b'\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04'

        # setup existing request
        d = client._build_response(0x00)
        d.add_done_callback(lambda v: out.append(v))

        client.on_receive(data)
        self.assertTrue(isinstance(out[0].result(), ReadCoilsResponse))
        data = b''
        out = []
        d = client._build_response(0x01)
        client.on_receive(data)
        d.add_done_callback(lambda v: out.append(v))
        self.assertFalse(out)

    def testClientExecute(self):
        ''' Test the client client execute method '''
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        client.stream = Mock()
        client.stream.write = Mock()

        request = ReadCoilsRequest(1, 1)
        d = client.execute(request)
        tid = request.transaction_id
        self.assertEqual(d, client.transaction.getTransaction(tid))

    def testClientHandleResponse(self):
        ''' Test the client client handles responses '''
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        client._handle_response(None)
        client._handle_response(reply)

        # handle existing cases
        d = client._build_response(0x00)
        d.add_done_callback(lambda v: out.append(v))
        client._handle_response(reply)
        self.assertEqual(out[0].result(), reply)

    def testClientBuildResponse(self):
        ''' Test the udp client client builds responses '''
        client = BaseTornadoClient()
        self.assertEqual(0, len(list(client.transaction)))

        def handle_failure(failure):
            exc = failure.exception()
            self.assertTrue(isinstance(exc, ConnectionException))
        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)
        self.assertEqual(0, len(list(client.transaction)))

        client._connected = True
        d = client._build_response(0x00)
        self.assertEqual(1, len(list(client.transaction)))

    #-----------------------------------------------------------------------#
    # Test TCP Client client
    #-----------------------------------------------------------------------#
    def testTcpClientInit(self):
        ''' Test the udp client client initialize '''
        client = AsyncModbusTCPClient()
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = AsyncModbusTCPClient(framer=framer)
        self.assertTrue(framer is client.framer)

    def testTcpClientConnect(self):
        ''' Test the client client connect '''
        client = AsyncModbusTCPClient(port=5020)
        self.assertTrue(client.port, 5020)
        self.assertFalse(client._connected)
        client.connect()
        self.assertTrue(client._connected)

    def testTcpClientDisconnect(self):
        ''' Test the client client disconnect '''
        client = AsyncModbusTCPClient(port=5020)
        client.connect()

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        self.assertTrue(client._connected)
        client.close()
        self.assertFalse(client._connected)


    #-----------------------------------------------------------------------#
    # Test Serial Client client
    #-----------------------------------------------------------------------#
    def testSerialClientInit(self):
        ''' Test the udp client client initialize '''
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP, framer=ModbusRtuFramer(ClientDecoder()), port="/dev/ptyp0")
        self.assertEqual(0, len(list(client.transaction)))
        print(isinstance(client.framer, ModbusRtuFramer))
        self.assertTrue(isinstance(client.framer, ModbusRtuFramer))

        framer = object()
        client = AsyncModbusSerialClient(framer=framer)
        self.assertTrue(framer is client.framer)

    def testSerialClientConnect(self):
        ''' Test the client client connect '''
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port="/dev/ptyp0")
        self.assertTrue(client.port, "/dev/ptyp0")
        self.assertFalse(client._connected)
        client.connect()
        self.assertTrue(client._connected)

    def testSerialClientDisconnect(self):
        ''' Test the client client disconnect '''
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port="/dev/ptyp0")
        client.connect()

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        self.assertTrue(client._connected)
        client.close()
        self.assertFalse(client._connected)

    def testSerialClientExecute(self):
        ''' Test the client client execute method '''
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port="/dev/ptyp0")
        client.connect()
        client.stream = Mock()
        client.stream.write = Mock()

        request = ReadCoilsRequest(1, 1)
        d = client.execute(request)
        tid = request.transaction_id
        self.assertEqual(d, client.transaction.getTransaction(tid))

    def testSerialClientHandleResponse(self):
        ''' Test the client client handles responses '''
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port="/dev/ptyp0")
        client.connect()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        client._handle_response(None)
        client._handle_response(reply)

        # handle existing cases
        d = client._build_response(0x00)
        d.add_done_callback(lambda v: out.append(v))
        client._handle_response(reply)
        self.assertEqual(out[0].result(), reply)

    def testSerialClientBuildResponse(self):
        ''' Test the udp client client builds responses '''
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port="/dev/ptyp0")
        self.assertEqual(0, len(list(client.transaction)))

        def handle_failure(failure):
            exc = failure.exception()
            self.assertTrue(isinstance(exc, ConnectionException))
        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)
        self.assertEqual(0, len(list(client.transaction)))

        client._connected = True
        d = client._build_response(0x00)
        self.assertEqual(1, len(list(client.transaction)))


    #-----------------------------------------------------------------------#
    # Test Udp Client client
    #-----------------------------------------------------------------------#

    def testUdpClientInit(self):
        ''' Test the udp client client initialize '''
        client = AsyncModbusUDPClient()
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = AsyncModbusUDPClient(framer=framer)
        self.assertTrue(framer is client.framer)

    #-----------------------------------------------------------------------#
    # Test Client Factories
    #-----------------------------------------------------------------------#

    def testModbusClientFactory(self):
        ''' Test the base class for all the clients '''
        factory = ModbusClientFactory()
        self.assertTrue(factory is not None)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
