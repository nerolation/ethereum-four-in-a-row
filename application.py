from flask import Flask, request, redirect, logging, make_response, json, render_template, Response, url_for
from flask_cors import CORS, cross_origin
import hashlib
from web3 import Web3, exceptions
import random
import boto3
import csv
import io, os
infurltest = "https://ropsten.infura.io/v3/c81785f09a5c4bde9727c8979e0aad70"
web3 = Web3(Web3.HTTPProvider(infurltest))
# Initialize flask an other global variables
application = Flask(__name__)
cors = CORS(application)
application.config['CORS_HEADERS'] = 'Content-Type'



@application.route('/')
@cross_origin()
def render_index():
    return render_template("index.html", pk = pk, users = USERS)

@application.route('/getBoard', methods=['POST'])
@cross_origin()
def get_board():
    bo = []
    u = None
    a = None
    player = None
    u = request.data.decode("utf-8")
    a = request.cookies['addr']
    ca = CONTRACT.functions.getBoard().call({'from': a})
    bo = []
    for i in ca[0]:
        for j in i:
            bo.append(j)
    try:
        player = ca[1].split(" ")[1]
    except:
        player = 0
    return (json.dumps([bo,player]), 200)

@application.route('/getGame', methods=['POST'])
@cross_origin()
def get_game():
    a = request.cookies['addr']
    pay = json.dumps((CONTRACT.functions.getGame().call({'from': a})))
    return (pay, 200)

@application.route('/claimWin', methods=['POST'])
@cross_origin()
def claim_win():
    global USERS, GAMES
    jsdata = request.data
    u, p1 = jsdata.decode('ascii').split(",")
    a = request.cookies['addr']
    pay = json.dumps(CONTRACT.functions.claimWin().call({'from': a}))

    if pay == "false":
        pass
    elif pay == "true":
        pk = s3.get_object(Bucket="nerolationxi", Key="connect-four/" + u)["Body"].read().decode("utf-8")
        ac = web3.eth.account.privateKeyToAccount(pk)
        tx = CONTRACT.functions.claimWin().buildTransaction(
            {'from': str(ac.address), 'nonce': web3.eth.getTransactionCount(ac.address)})
        raw_tx = ac.signTransaction(tx)
        tx_hash = web3.eth.sendRawTransaction(raw_tx.rawTransaction).hex()
        web3.eth.waitForTransactionReceipt(tx_hash)
        for i in USERS.keys():
            if USERS[i]["address"] == p1:
                jk = USERS[i]["username"]
                break

        GAMES[jk]["open"] = False
        GAMES[jk]["ended"] = True
        GAMES[jk]["open"] = False
        p1_u = GAMES[jk]["p1"]['username']
        p2_u = GAMES[jk]["p2"]['username']

        if u == p1_u:
            USERS[p1_u]["wonGames"] += 1
            USERS[p1_u]["openGame"] = None
            USERS[p2_u]["lostGames"] += 1
            USERS[p2_u]["openGame"] = None
        elif u == p2_u:
            USERS[p2_u]["wonGames"] += 1
            USERS[p2_u]["openGame"] = None
            USERS[p1_u]["lostGames"] += 1
            USERS[p1_u]["openGame"] = None
        aws_sync(data=json.dumps(USERS).encode(), filename='users.json')
        aws_sync(data=json.dumps(GAMES).encode(), filename='games.json')
    return (pay, 200)

@application.route('/init', methods = ['POST'])
@cross_origin()
def get_post_init():
    global GAMES, USERS
    u = request.data.decode("utf-8")
    try:
        pk = s3.get_object(Bucket = "nerolationxi", Key = "connect-four/" + u)["Body"].read().decode("utf-8")
        ac = web3.eth.account.privateKeyToAccount(pk)
        tx = CONTRACT.functions.initGame().buildTransaction({'from': str(ac.address), 'nonce':web3.eth.getTransactionCount(ac.address)})
        raw_tx = ac.signTransaction(tx)
        tx_hash = web3.eth.sendRawTransaction(raw_tx.rawTransaction).hex()
        web3.eth.waitForTransactionReceipt(tx_hash)
    except (exceptions.SolidityError, ValueError) as error:
        return str(error)
    GAMES[u] = GAME(USER(u, ac.address).__dict__).__dict__
    USERS[u]['openGame'] = True
    aws_sync(data = json.dumps(GAMES), filename = "games.json")
    return tx_hash

@application.route('/join', methods = ['POST'])
@cross_origin()
def get_post_join():
    global GAMES, USERS
    jsdata = request.data
    u, ja = jsdata.decode('ascii').split(",")
    pk = s3.get_object(Bucket = "nerolationxi", Key = "connect-four/" + u)["Body"].read().decode("utf-8")
    ac = web3.eth.account.privateKeyToAccount(pk)
    try:
        tx = CONTRACT.functions.joinGame(ja).buildTransaction({'from': str(ac.address), 'nonce':web3.eth.getTransactionCount(ac.address)})
        raw_tx = ac.signTransaction(tx)
        tx_hash = web3.eth.sendRawTransaction(raw_tx.rawTransaction).hex();
        web3.eth.waitForTransactionReceipt(tx_hash)
    except (exceptions.SolidityError, ValueError, exceptions.ValidationError) as error:
        if "Could not identify" in str(error):
            error = "execution reverted: Invalid Address"
        return str(error)
    for i in USERS.keys():
        if USERS[i]["address"] == ja:
            jk = USERS[i]["username"]
            break
    if u in USERS.keys():
        pass
    else:
        USERS[u] = USER(u, ac.address).__dict__
    GAMES[jk]["p2"] = USERS[u]
    USERS[u]['openGame'] = True
    aws_sync(data = json.dumps(GAMES), filename = "games.json")
    return tx_hash

@application.route('/randomgame', methods = ['POST'])
@cross_origin()
def get_post_rand():
    global GAMES, USERS
    tx_hash_i = None
    tx_hash_j = None
    u = request.data.decode("utf-8")
    pk = s3.get_object(Bucket = "nerolationxi", Key = "connect-four/" + u)["Body"].read().decode("utf-8")
    ac = web3.eth.account.privateKeyToAccount(pk)
    err=""
    #Init
    try:
        tx = CONTRACT.functions.initGame().buildTransaction(
            {'from': str(ac.address), 'nonce': web3.eth.getTransactionCount(ac.address)})
        raw_tx_init = ac.signTransaction(tx)
        tx_hash_i = web3.eth.sendRawTransaction(raw_tx_init.rawTransaction).hex()
        web3.eth.waitForTransactionReceipt(tx_hash_i)
    except (exceptions.SolidityError, ValueError) as error:
        err = str(error)
    #Join
    try:
        tx = CONTRACT.functions.joinGame(ac.address).buildTransaction(
            {'from': str(IMP.address), 'nonce': web3.eth.getTransactionCount(IMP.address)})
        raw_tx_join = IMP.signTransaction(tx)
        tx_hash_j = web3.eth.sendRawTransaction(raw_tx_join.rawTransaction).hex()
        web3.eth.waitForTransactionReceipt(tx_hash_j)
    except (exceptions.SolidityError, ValueError) as error:
        return err
    GAMES[u] = GAME(USER(u, ac.address).__dict__, USER('randy', IMP.address).__dict__).__dict__
    aws_sync(data = json.dumps(GAMES), filename = "games.json")
    USERS[u]['openGame'] = True
    return (json.dumps([tx_hash_i,tx_hash_j]),200)

@application.route('/move', methods = ['POST'])
@cross_origin()
def get_post_move():
    global GAMES, USERS
    jsdata = request.data
    m,u,p1 = jsdata.decode('ascii').split(",")
    pk = s3.get_object(Bucket = "nerolationxi", Key = "connect-four/" + u)["Body"].read().decode("utf-8")
    ac = web3.eth.account.privateKeyToAccount(pk)
    for i in USERS.keys():
        if USERS[i]["address"] == p1:
            jk = USERS[i]["username"]
            break
    try:
        tx = CONTRACT.functions.move(int(m)).buildTransaction({'from': str(ac.address), 'nonce':web3.eth.getTransactionCount(ac.address)})
        raw_tx = ac.signTransaction(tx)
        GAMES[jk]["moves"].append(int(m))
        aws_sync(data = json.dumps(GAMES), filename = "games.json")
        tx_hash = web3.eth.sendRawTransaction(raw_tx.rawTransaction).hex()
        web3.eth.waitForTransactionReceipt(tx_hash)
        return (json.dumps([tx_hash]),200)
    except (exceptions.SolidityError, ValueError) as error:
        return json.dumps([str(error)])
    return "FAIL"

@application.route('/moverand', methods = ['POST'])
@cross_origin()
def get_post_moverand():
    global GAMES, USERS
    err = ""
    jsdata = request.data
    m,u,p1 = jsdata.decode('ascii').split(",")
    pk = s3.get_object(Bucket = "nerolationxi", Key = "connect-four/" + u)["Body"].read().decode("utf-8")
    ac = web3.eth.account.privateKeyToAccount(pk)
    try:
        tx = CONTRACT.functions.move(int(m)).buildTransaction({'from': str(ac.address), 'nonce':web3.eth.getTransactionCount(ac.address)})
        raw_tx = ac.signTransaction(tx)
        tx_hash_m1 = web3.eth.sendRawTransaction(raw_tx.rawTransaction).hex()
        GAMES[u]["moves"].append(m)
        web3.eth.waitForTransactionReceipt(tx_hash_m1, timeout=180)

    except (exceptions.SolidityError, ValueError) as error:
        err = str(error)
        tx_hash_m1 = "undefined"
        print(err)
    try:
        ra = random.randint(0,6)
        tx = CONTRACT.functions.move(ra).buildTransaction(
            {'from': IMP.address, 'nonce': web3.eth.getTransactionCount(IMP.address)})
        raw_tx = IMP.signTransaction(tx)
        tx_hash_m2 = web3.eth.sendRawTransaction(raw_tx.rawTransaction).hex()
        GAMES[u]["moves"].append(ra)
        web3.eth.waitForTransactionReceipt(tx_hash_m2, timeout=180)
        aws_sync(data = json.dumps(GAMES), filename = "games.json")
        return (json.dumps([tx_hash_m1,tx_hash_m2, ra]),200)
    except (exceptions.SolidityError, ValueError) as error:
        err = err + " AND " + str(error)
    print("DOUBLE ERROR")
    aws_sync(data = json.dumps(GAMES), filename = "games.json")
    return (err,200)


@application.route('/user', methods = ['GET', 'POST'])
@cross_origin()
def get_post_user():
    global pk, USERS
    u = request.form['username']
    pk = request.form['pk']
    created = b'0'
    if u not in USERS.keys():
        if not (pk):
            a = web3.eth.account.create(hashlib.sha256((u + str(random.randint(1, 10000000))
                                                        + str(random.randint(1, 10000000))
                                                        + str(random.randint(1, 10000000))).encode('utf-8')).hexdigest().encode())
        else:
            a = web3.eth.account.privateKeyToAccount(pk)
        pk = a.privateKey.hex()
        acc = a.address
        USERS[u] = USER(u, acc).__dict__
        s_buf = io.StringIO(pk)
        aws_sync(data = s_buf.getvalue(), filename=u)
        aws_sync(data = json.dumps(USERS).encode(), filename='users.json')
        created = b'1'
    else:
        acc = USERS[u]['address']
    resp = make_response(redirect('/', code=302))
    resp.set_cookie("login", b'1', max_age=60 * 60, samesite='Lax')
    resp.set_cookie("user", u.encode(), max_age=60 * 60, samesite='Lax')
    resp.set_cookie("addr", acc, max_age=60 * 60, samesite='Lax')
    resp.set_cookie("c", created, max_age=30, samesite='Lax')
    return resp

def aws_sync(filename, data=None, method = "put"):
    if method == "put":
        s3.put_object(Body=data, Bucket="nerolationxi", Key="connect-four/" + filename)
    elif method == "get":
        return s3.get_object(Bucket="nerolationxi", Key="connect-four/" + filename)["Body"].read().decode("utf-8")
    return True


acc = None
pk = None

with open(".aws/credentials") as c:
    reader = csv.reader(c)
    creds = [i for i in reader]
s3 = boto3.client('s3', aws_access_key_id=creds[0][0],aws_secret_access_key=creds[0][1])

CONTRACT_ADDRESS, CONTRACT_ABI = (web3.toChecksumAddress('0x0Ca1Fd93C43286A8e9e86bc0A659E6719101F3ac'),json.loads('[{"inputs":[],"name":"claimWin","outputs":[{"internalType":"bool","name":"win","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"p1","type":"address"},{"indexed":true,"internalType":"bytes32","name":"lobby","type":"bytes32"}],"name":"GameCreation","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"winner","type":"address"},{"indexed":true,"internalType":"address","name":"looser","type":"address"},{"indexed":false,"internalType":"bytes32","name":"lobby","type":"bytes32"}],"name":"GameEnd","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"p2","type":"address"},{"indexed":true,"internalType":"bytes32","name":"lobby","type":"bytes32"}],"name":"GameJoin","type":"event"},{"inputs":[],"name":"initGame","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_addr","type":"address"}],"name":"joinGame","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint8","name":"_move","type":"uint8"}],"name":"move","outputs":[],"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"p","type":"address"},{"indexed":true,"internalType":"bytes32","name":"lobby","type":"bytes32"},{"indexed":false,"internalType":"uint8","name":"move","type":"uint8"}],"name":"Move","type":"event"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"games","outputs":[{"internalType":"address","name":"player1","type":"address"},{"internalType":"address","name":"player2","type":"address"},{"internalType":"bool","name":"alt","type":"bool"},{"internalType":"bool","name":"ended","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getBoard","outputs":[{"internalType":"uint8[7][5]","name":"","type":"uint8[7][5]"},{"internalType":"string","name":"turn","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getGame","outputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"bool","name":"","type":"bool"},{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint8","name":"","type":"uint8"}],"name":"lobby","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"}]'))
CONTRACT = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
PK = os.environ["PK"]
IMP = web3.eth.account.privateKeyToAccount(PK)

class GAME:
    def __init__(self, p1, p2 = None):
        self.p1 = p1
        self.p2 = p2
        self.moves = []
        self.open = True
        self.ended = False

class USER:
    def __init__(self, username, address):
        self.username = username
        self.address = address
        self.openGame = None
        self.wonGames = 0
        self.lostGames = 0

USERS = {}
GAMES = {}


try:
    GAMES = json.loads(aws_sync(filename="games.json", method = "get"))
except:
    pass
try:
    USERS = json.loads(aws_sync(filename="users.json", method = "get"))
except:
    pass
if "randy" not in USERS.keys():
    USERS['randy'] = USER("randy", IMP.address).__dict__


if __name__ == '__main__':
   application.run(debug=True)
