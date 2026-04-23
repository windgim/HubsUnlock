import sys
import os
import grpc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto'))

from app.proxyman.command.command_pb2_grpc import HandlerServiceStub
from app.proxyman.command.command_pb2 import AlterInboundRequest, AddUserOperation, RemoveUserOperation
from common.serial.typed_message_pb2 import TypedMessage
from proxy.vless.account_pb2 import Account
from dotenv import load_dotenv

load_dotenv()

class Handler:
    def __init__(self):
        host = os.environ.get('XRAY_HOST')
        port = os.environ.get('XRAY_PORT')
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = HandlerServiceStub(self.channel)
        self.tag = 'vless-in'
    
    def add_user(self, email, uid):
        account = Account()
        account.id = uid
        account.flow = ""
        account.encryption = "none"
        
        account_msg = TypedMessage()
        account_msg.type = "xray.proxy.vless.Account"
        account_msg.value = account.SerializeToString()
        
        op = AddUserOperation()
        op.user.email = email
        op.user.account.CopyFrom(account_msg)
        
        op_msg = TypedMessage()
        op_msg.type = "xray.app.proxyman.command.AddUserOperation"
        op_msg.value = op.SerializeToString()
        
        self.stub.AlterInbound(AlterInboundRequest(tag=self.tag, operation=op_msg))
    
    def remove_user(self, email):
        op = RemoveUserOperation()
        op.email = email
        
        op_msg = TypedMessage()
        op_msg.type = "xray.app.proxyman.command.RemoveUserOperation"
        op_msg.value = op.SerializeToString()
        
        self.stub.AlterInbound(AlterInboundRequest(tag=self.tag, operation=op_msg))
