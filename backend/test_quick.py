import asyncio
import os
from kerma.config import Config
from kerma.storage.database import Database
from kerma.core.blockchain import Blockchain

config = Config()
db = Database('test_chain.db')
bc = Blockchain(config, db)
bc.initialize()

print(f"Chain height: {bc.get_height()}")
print(f"Tip ID: {bc.get_tip_id()}")
chain = bc.get_chain(5)
print(f"Chain length: {len(chain)}")
for b in chain:
    print(f"  Block {b['height']}: {b['id'][:16]}...")

os.unlink('test_chain.db')
print("Backend core works!")
