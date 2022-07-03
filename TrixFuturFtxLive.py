from numpy import integer
from cBot_perp_ftx import cBot_perp_ftx
import ta
import pandas as pd
import argparse
import sys, getopt
import json

# -- Condition to open Market LONG --
def openLongCondition(row,rsiMax):
    if row['TRIX_HISTO'] > 0 and row['STOCH_RSI'] <= rsiMax:
        return True
    else:
        return False

# -- Condition to close Market LONG --
def closeLongCondition(row,rsiMin):
    if row['TRIX_HISTO'] < 0 and row['STOCH_RSI'] >= rsiMin:
        return True
    else:
        return False

# -- Condition to open Market SHORT --
def openShortCondition(row,rsiMin):
    if (row['TRIX_HISTO'] < 0
    and row['EMA6'] > row['EMA1']
    and row['STOCH_RSI'] > rsiMin ):
        return True
    else:
        return False

# -- Condition to close Market SHORT --
def closeShortCondition(row,rsiMax):
    if (row['TRIX_HISTO'] > 0
      and row['STOCH_RSI'] < rsiMax):
        return True
    else:
        return False


def main(argv):
    tokenDef = None

    #print(str(argv))

    parser = argparse.ArgumentParser(description="TrixFuturFtxLive",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--token",        required=True,   help="token name, Exemple BTC,ETH,SOL")
    parser.add_argument("-a", "--accountName",  required=True,   help="Account name to use for trading")
    parser.add_argument("-W", "--RsiWindow",    required=False,  type=int,                             help="Rsi window")
    parser.add_argument("-L", "--TrixLength",   required=False,  type=int,                              help="Trix Length")
    parser.add_argument("-S", "--TrixSignal",   required=False,  type=int,                             help="Trix Signal")
    parser.add_argument("-s", "--stoplost",     required=False,  type=float,                                        help="Stoplost allowed in %")
    parser.add_argument("-l", "--Level",        required=False,  type=int,              default="1",                help="Level (Attention,risque de liquidation)")
    parser.add_argument("-n", "--NoShort",      required=False,                         action="store_true",        help="Only long trades allowed")

    args = vars(parser.parse_args())
    print(args)


    # -- Strategy variable --
    perpSymbol = None
    tokenName = None
    leverage = 1
    trixLength = 9
    trixSignal = 21
    rsiWindow = 15
    stoplost = None
    accountName = None
    noShort = False
    rsiMin = 0.28
    rsiMax = 0.7

    if( "token" in args.keys()):
        perpSymbol = args["token"] + "-PERP"
        tokenName = args["token"]

    if args["NoShort"]:
        noShort = True


    if( "accountName" in args.keys()):
        accountName = args["accountName"]

    if ("stoplost" in args.keys() and args["stoplost"] != None):
        stoplost = args["stoplost"]   

    if ("Level" in args.keys()):
        leverage = args["Level"]


    # Paramètres de la stratégie

    if ("RsiWindow" in args.keys() and args["RsiWindow"] != None):
        rsiWindow = args["RsiWindow"] 
    
    if ("TrixLength" in args.keys() and args["TrixLength"] != None):
        trixLength = args["TrixLength"] 
    
    if ("TrixSignal" in args.keys() and args["TrixSignal"] != None):
        trixSignal = args["TrixSignal"] 



    # Test des paramètres obligatoires

    if(accountName == None):
        print("An account name is attempted via parameter -t or --token, Exemple -t BTC")
        sys.exit()

    if(perpSymbol == None):
        print("A token name is attempted via parameter -a or --accountName, Exemple -a trixsubaccount")
        sys.exit()


    # On charge les infos de connexion du compte sélectionné
    account_to_select = accountName

    f = open(
        "secret.json",
    )
    secret = json.load(f)
    f.close()

    try:
        accountInfo = secret[account_to_select]
        apiKeyAcct = secret[account_to_select]["apiKey"]
        secretAcct = secret[account_to_select]["secret"]
    except BaseException as err:
        print("No Api info found for account : ", account_to_select)
        sys.exit()

    if(len(apiKeyAcct) == 0 or len(secretAcct) == 0):
        print("No Api info found for account : ", account_to_select )
        sys.exit()


    # On charge la définition des tokens

    try:
        f = open(
            "TokensDef.json",
        )
        tokenDef = json.load(f)
        f.close()

        tokenInfo = None
        DefaultInfo = None

        for i in tokenDef:

            if i == "DEFAULT":
                DefaultInfo = tokenDef['DEFAULT']

                if 'rsiWindow' in DefaultInfo:
                    rsiWindow = int(DefaultInfo['rsiWindow'])
                if 'trixLength' in DefaultInfo:
                    trixLength = int(DefaultInfo['trixLength'])
                if 'trixSignal' in DefaultInfo:
                    trixSignal = int(DefaultInfo['trixSignal'])
                if 'rsiMin' in DefaultInfo:
                    rsiMin = float(DefaultInfo['rsiMin'])
                if 'rsiMax' in DefaultInfo:
                    rsiMax = float(DefaultInfo['rsiMax'])


            if i == perpSymbol:
                tokenInfo   = tokenDef[perpSymbol]
                if 'rsiWindow' in tokenInfo:
                    rsiWindow   = int(tokenInfo['rsiWindow'])
                if 'trixLength' in tokenInfo:
                    trixLength  = int(tokenInfo['trixLength'])
                if 'trixSignal' in tokenInfo:
                    trixSignal  = int(tokenInfo['trixSignal'])
                if 'rsiMin' in tokenInfo :
                    rsiMin      = float(tokenInfo['rsiMin'])
                if 'rsiMax' in tokenInfo:
                    rsiMax      = float(tokenInfo['rsiMax'])
                break
    except BaseException as Err:
        print("Fail to load tokens definition, use default configuration")

    ftx = cBot_perp_ftx(
        apiKey=apiKeyAcct,
        secret=secretAcct,
        subAccountName=accountName         #'Trix_bot1'
    )


    # -- Price Data --
    df = ftx.get_last_historical(perpSymbol, '1h', 250)

    # -- indicators --
    df['EMA1']= ta.trend.ema_indicator(close=df['close'], window=7)
    df['EMA2']= ta.trend.ema_indicator(close=df['close'], window=30)
    df['EMA3']= ta.trend.ema_indicator(close=df['close'], window=50)
    df['EMA4']= ta.trend.ema_indicator(close=df['close'], window=100)
    df['EMA5']= ta.trend.ema_indicator(close=df['close'], window=121)
    df['EMA6']= ta.trend.ema_indicator(close=df['close'], window=218)



    df['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=df['close'], window=trixLength), window=trixLength), window=trixLength)
    df['TRIX_PCT'] = df["TRIX"].pct_change()*100
    df['TRIX_SIGNAL'] = ta.trend.sma_indicator(df['TRIX_PCT'],trixSignal)
    df['TRIX_HISTO'] = df['TRIX_PCT'] - df['TRIX_SIGNAL']
    df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=rsiWindow, smooth1=3, smooth2=3)
    #print(df)

    # -- Get USD amount on Sub Account --
    usdAmount = ftx.get_balance_of_one_coin('USD')
    print("Solde en $: " , usdAmount)

    # -- Get actual price --
    actualPrice = df.iloc[-1]['close']

    if len(ftx.get_open_position([perpSymbol])) != 0:
        # -- Check if you have a LONG open --
        if ftx.get_open_position([perpSymbol])[0]['side'] == 'long':
            # -- Check if you have to close your LONG --
            if closeLongCondition(df.iloc[-2], rsiMin):
                ftx.close_all_open_position([perpSymbol])
                ftx.cancel_all_open_order(perpSymbol)
                print('Close my LONG position at ', actualPrice)
            else:
                print("A LONG is running and I don't want to stop it")
        # -- Check if you have a SHORT open --
        elif ftx.get_open_position([perpSymbol])[0]['side'] == 'short':
            if closeShortCondition(df.iloc[-2], rsiMax):
                ftx.close_all_open_position([perpSymbol])
                ftx.cancel_all_open_order(perpSymbol)
                print('Close my SHORT position at ', actualPrice)
            else:
                print("A SHORT is running and I don't want to stop it")


    # -- Check if you have no position running --
    if len(ftx.get_open_position([perpSymbol])) == 0:
        # -- Check if you have to open a LONG --
        if openLongCondition(df.iloc[-2], rsiMax):
            # -- Cancel all order (stop loss) --
            ftx.cancel_all_open_order(perpSymbol)
            # -- Define the quantity max of token from your usd balance --
            quantityMax = float(usdAmount)/actualPrice
            
            #Pour debugger
            #quantityMax = 0
            # -- Create a market order Long --
            longOrder = ftx.place_market_order(
                perpSymbol,
                'buy',
                quantityMax,
                leverage
            )
            print("Open a market LONG at", actualPrice)
                        
            # -- Create a market stop loss -3% --
            if(stoplost != None):
                stopLoss = ftx.place_market_stop_loss(
                    perpSymbol,
                    'sell',
                    quantityMax,
                    actualPrice - (stoplost /100 ) * actualPrice,
                    leverage
                )
                print("Place a Stop Loss at ", actualPrice - (stoplost /100 ) * actualPrice)

        elif openShortCondition(df.iloc[-2], rsiMin):
            # -- Cancel all order (stop loss) --
            ftx.cancel_all_open_order(perpSymbol)
            # -- Define the quantity max of token from your usd balance --
            quantityMax = float(usdAmount)/actualPrice

            #Pour debugger
            #quantityMax = 0
            # -- Create a market order Long --
            shortOrder = ftx.place_market_order(
                perpSymbol,
                'sell',
                quantityMax,
                leverage
            )
            print("Open a market SHORT at", actualPrice)
            
            if(stoplost != None):
                # -- Create a market stop loss -3% --
                stopLoss = ftx.place_market_stop_loss(
                    perpSymbol,
                    'buy',
                    quantityMax,
                    actualPrice + (stoplost /100 ) * actualPrice,
                    leverage
                )
                print("Place a Stop Loss at", actualPrice + (stoplost /100 ) * actualPrice)

        else:
            print("No opportunity to take")



if __name__=="__main__":
    main(sys.argv[1:])
