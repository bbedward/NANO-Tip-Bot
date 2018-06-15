#!/usr/bin/awk BEGIN{a=ARGV[1];sub(/[a-z_.]+$/,"venv/bin/python",a);system(a"\t"ARGV[1])}
import db
import argparse
import sys

parser = argparse.ArgumentParser(description="Utilities for Graham TipBot")
parser.add_argument('-u', '--get-unprocessed', action='store_true',  help='Display number of un-processed transactions')
parser.add_argument('-r', '--replay', action='store_true', help='Replay un-processed/failed transactions')
parser.add_argument('-l', '--lookup', type=str, help='Lookup information about a specific block hash', default=None)
options = parser.parse_args()

@db.db.connection_context()
def display_unprocessed():
    unprocessed = (db.Transaction.select()
                    .where((db.Transaction.processed == False) & (db.Transaction.giveawayid == 0)).count())
    unprocessed_giveaway = (db.Transaction.select()
                    .where((db.Transaction.processed == False) & (db.Transaction.giveawayid != 0)).count())
    print("Unprocessed/Pending: {0} \n Pending Giveaway: {1}".format(unprocessed, unprocessed_giveaway))

@db.db.connection_context()
def replay_unprocessed():
    unprocessed = (db.Transaction.select()
                    .where((db.Transaction.processed == False) & (db.Transaction.giveawayid == 0)))
    for t in unprocessed:
        print("replaying transaction with UID {0}".format(t.uid))
        db.process_transaction(t)

@db.db.connection_context()
def tran_info(hash):
    try:
        tran = db.Transaction.select().where(db.Transaction.tran_id == hash).get()
        source_user = db.User.select().where(db.User.wallet_address == tran.source_address).get()
        print('Tran UID: {0}'.format(tran.uid))
        print('Source user ID: {0}, name: {1}, address: {2}'.format(source_user.user_id, source_user.user_name, source_user.wallet_address))
        print('Amount: {0}'.format(tran.amount))
        try:
            target = db.User.select().where(db.User.wallet_address == tran.to_address).get()
            print('Recipient user ID: {0}, name: {1}, address: {2}'.format(target.user_id, target.user_name, target.wallet_address))
        except db.User.DoesNotExist:
            print('Not a tip, was a withdraw to this address {0}'.format(tran.to_address))
    except db.Transaction.DoesNotExist:
        print("I do not have any transactions with block hash {0}".format(hash))

if __name__ == '__main__':
    if options.get_unprocessed:
        display_unprocessed()
    elif options.replay:
        replay_unprocessed()
    elif options.lookup is not None:
        tran_info(options.lookup)
    sys.exit(0)