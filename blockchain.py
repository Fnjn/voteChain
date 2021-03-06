from block import Block
from transaction import Transaction
import crypto
import utils

class Blockchain:

    def __init__(self, last_block = None):
        self.last_block = last_block


    def set_last_block(self, last_block):
        self.last_block = last_block


    def verify(self):
        block = self.last_block
        while(isinstance(block, Block)):
            pubkey = utils.lookupPubkey(block.miner)
            if verification(pubkey, bytes(block), block.signature):
                return False
            if build_merkle_tree(True)[1] != block.merkle_tree[1]:
                return False

            data = bytes(block)
            nonce_b = nonce.to_bytes(16, byteorder = 'big')
            res = crypto.dhash(data + nonce_b)
            if int.from_bytes(res[:LEADING_ZEROS], byteorder = 'big') != 0:
                return False

        return True


    def __len__(self):
        n = 0
        block = self.last_block
        while(isinstance(block, Block)):
            n += 1
            block = block.prev_block
        return n
